"""Tang Device: gia lap thiet bi kho (GT-01, GT-02, HH-01, AGV-01, AGV-02).

Moi thiet bi la mot MQTT client rieng, tai khoan rieng (ACL chi cho ghi vao chu
de mang ma cua chinh no). Cau truc theo vong doi firmware ESP32:
khoi dong -> ket noi -> gui trang thai TRUC_TUYEN (retain) -> doc/gui;
mat ket noi -> dem ban tin -> ket noi lai -> gui lai dung thu tu.
Hop dong ban tin: docs/contracts/*.schema.json (khong mang logic nghiep vu).
"""
import json
import logging
import random
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

log = logging.getLogger("device")


def bay_gio() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class NhatKy:
    """Nhat ky su kien dung chung cho bang dieu khien (an toan da luong)."""

    def __init__(self, toi_da: int = 300):
        self._q = deque(maxlen=toi_da)
        self._khoa = threading.Lock()

    def ghi(self, ma_tb: str, noi_dung: str) -> None:
        with self._khoa:
            self._q.appendleft((datetime.now().strftime("%H:%M:%S"), ma_tb, noi_dung))
        log.info("%s: %s", ma_tb, noi_dung)

    def doc(self) -> list[tuple[str, str, str]]:
        with self._khoa:
            return list(self._q)


class ThietBi:
    KEEPALIVE = 5            # giay; broker phat Last Will sau ~1,5 x keepalive khi mat ket noi bat thuong
    GIU_PHIEN = False        # clean_session=False de nhan lenh QoS 1 da xep hang khi offline

    def __init__(self, ma_tb: str, host: str, port: int, mat_khau: str, nhat_ky: NhatKy):
        self.ma_tb, self.host, self.port, self.mat_khau = ma_tb, host, port, mat_khau
        self.nhat_ky = nhat_ky
        self.bo_dem: deque[tuple[str, str]] = deque()   # ban tin chua gui duoc
        self._khoa = threading.Lock()
        self.truc_tuyen = False
        self.client: mqtt.Client | None = None

    # ---------------- vong doi ket noi
    def _tao_client(self) -> mqtt.Client:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.ma_tb,
                        clean_session=not self.GIU_PHIEN, protocol=mqtt.MQTTv311)
        c.username_pw_set(self.ma_tb, self.mat_khau)
        c.will_set(f"kho/thietbi/{self.ma_tb}/trang-thai",
                   json.dumps({"v": 1, "maTB": self.ma_tb, "trangThai": "NGOAI_TUYEN"}), qos=1, retain=True)
        c.on_connect = self._khi_ket_noi
        c.on_disconnect = self._khi_mat_ket_noi
        c.on_message = self._khi_nhan
        c.reconnect_delay_set(1, 5)
        return c

    def bat_dau(self) -> None:
        self.client = self._tao_client()
        self.client.connect_async(self.host, self.port, keepalive=self.KEEPALIVE)
        self.client.loop_start()

    def _khi_ket_noi(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            self.nhat_ky.ghi(self.ma_tb, f"Kết nối bị từ chối: {reason_code}")
            return
        client.publish(f"kho/thietbi/{self.ma_tb}/trang-thai",
                       json.dumps({"v": 1, "maTB": self.ma_tb, "trangThai": "TRUC_TUYEN"}), qos=1, retain=True)
        self.dang_ky(client)
        with self._khoa:
            self.truc_tuyen = True
            ton = list(self.bo_dem)
            self.bo_dem.clear()
        self.nhat_ky.ghi(self.ma_tb, "Trực tuyến" + (f", gửi lại {len(ton)} bản tin đệm" if ton else ""))
        for chu_de, du_lieu in ton:   # gui lai dung thu tu
            client.publish(chu_de, du_lieu, qos=1)

    def _khi_mat_ket_noi(self, client, userdata, flags, reason_code, properties):
        with self._khoa:
            self.truc_tuyen = False
        self.nhat_ky.ghi(self.ma_tb, f"Mất kết nối ({reason_code})")

    def dang_ky(self, client) -> None:
        """Thiet bi can nhan lenh (AGV) dang ky chu de o day."""

    def _khi_nhan(self, client, userdata, msg) -> None:
        pass

    def phat(self, chu_de: str, ban_tin: dict) -> None:
        du_lieu = json.dumps(ban_tin, ensure_ascii=False)
        with self._khoa:
            if not self.truc_tuyen:
                self.bo_dem.append((chu_de, du_lieu))
                self.nhat_ky.ghi(self.ma_tb, f"Ngoại tuyến, đệm bản tin ({len(self.bo_dem)} trong bộ đệm)")
                return
            client = self.client
        client.publish(chu_de, du_lieu, qos=1)

    def mo_phong_mat_ket_noi(self, so_giay: float) -> None:
        """Ngat ket noi bat thuong (khong gui DISCONNECT) -> broker phat Last Will."""
        cu = self.client
        with self._khoa:
            self.truc_tuyen = False
        cu.loop_stop()
        sock = cu.socket()
        if sock:
            sock.close()
        self.nhat_ky.ghi(self.ma_tb, f"Mô phỏng mất kết nối {so_giay:.0f} giây")

        def ket_noi_lai():
            time.sleep(so_giay)
            self.bat_dau()
        threading.Thread(target=ket_noi_lai, daemon=True).start()

    def dung(self) -> None:
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()


class DauDocRFID(ThietBi):
    """Cong RFID (GT-01 nhap, GT-02 xuat) va dau doc cam tay (HH-01): cung mot hop dong doc-the."""

    def doc(self, ds_epc: list[str]) -> str:
        ma = str(uuid.uuid4())
        self.phat(f"kho/thietbi/{self.ma_tb}/doc-the", {
            "v": 1, "maBanTin": ma, "maTB": self.ma_tb, "thoiDiem": bay_gio(),
            "the": [{"maEPC": e, "cuongDo": random.randint(-70, -45)} for e in ds_epc]})
        self.nhat_ky.ghi(self.ma_tb, f"Đọc {len(ds_epc)} thẻ, bản tin {ma[:8]}")
        return ma


class AGV(ThietBi):
    GIU_PHIEN = True
    THOI_GIAN_CHAY = 3.0          # giay cho mot nhiem vu
    THOI_GIAN_MAT_KET_NOI = 12.0  # KB4: lon hon 1,5 x keepalive de broker kip phat Last Will

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.lenh_da_nhan: set[str] = set()
        self.loi_lan_toi = False        # kich ban KB4
        self.nhiem_vu_hien_tai: str | None = None

    def dang_ky(self, client) -> None:
        client.subscribe(f"kho/agv/{self.ma_tb}/lenh", qos=1)

    def _khi_nhan(self, client, userdata, msg) -> None:
        try:
            lenh = json.loads(msg.payload)
        except ValueError:
            return
        if lenh.get("maBanTin") in self.lenh_da_nhan:   # lenh gui lai (QoS 1) -> bo qua
            return
        self.lenh_da_nhan.add(lenh.get("maBanTin"))
        threading.Thread(target=self._thuc_hien, args=(lenh,), daemon=True).start()

    def _bao(self, ma_nvu: str, trang_thai: str, ma: str | None = None) -> dict:
        bt = {"v": 1, "maBanTin": ma or str(uuid.uuid4()), "maTB": self.ma_tb, "maNVu": ma_nvu,
              "trangThai": trang_thai, "thoiDiem": bay_gio()}
        self.phat(f"kho/agv/{self.ma_tb}/nhiem-vu", bt)
        return bt

    def _thuc_hien(self, lenh: dict) -> None:
        ma_nvu = lenh["maNVu"]
        self.nhiem_vu_hien_tai = ma_nvu
        self.nhat_ky.ghi(self.ma_tb, f"Nhận {ma_nvu}: {lenh['maKien']} {lenh['viTriDi']} → {lenh['viTriDen']}")
        time.sleep(0.5)
        self._bao(ma_nvu, "DANG_THUC_HIEN")
        if self.loi_lan_toi:   # KB4: mat ket noi giua chung, ban tin hoan thanh bi gui lai 2 lan
            self.loi_lan_toi = False
            self.mo_phong_mat_ket_noi(self.THOI_GIAN_MAT_KET_NOI)
            time.sleep(self.THOI_GIAN_CHAY)
            ma = str(uuid.uuid4())
            self._bao(ma_nvu, "HOAN_THANH", ma)
            self._bao(ma_nvu, "HOAN_THANH", ma)   # cung maBanTin: mo phong gui lai do khong nhan PUBACK
        else:
            time.sleep(self.THOI_GIAN_CHAY)
            self._bao(ma_nvu, "HOAN_THANH")
        self.nhat_ky.ghi(self.ma_tb, f"Hoàn thành {ma_nvu}")
        self.nhiem_vu_hien_tai = None


class QuanLyThietBi:
    def __init__(self, host: str, port: int, mat_khau: str):
        self.nhat_ky = NhatKy()
        tham_so = dict(host=host, port=port, mat_khau=mat_khau, nhat_ky=self.nhat_ky)
        self.thiet_bi: dict[str, ThietBi] = {
            "GT-01": DauDocRFID("GT-01", **tham_so),
            "GT-02": DauDocRFID("GT-02", **tham_so),
            "HH-01": DauDocRFID("HH-01", **tham_so),
            "AGV-01": AGV("AGV-01", **tham_so),
            "AGV-02": AGV("AGV-02", **tham_so),
        }

    def bat_dau(self) -> "QuanLyThietBi":
        for tb in self.thiet_bi.values():
            tb.bat_dau()
        return self

    def dung(self) -> None:
        for tb in self.thiet_bi.values():
            tb.dung()

    def doc(self, ma_tb: str, ds_epc: list[str]) -> str:
        tb = self.thiet_bi[ma_tb]
        if not isinstance(tb, DauDocRFID):
            raise ValueError(f"{ma_tb} không phải đầu đọc RFID")
        return tb.doc(ds_epc)
