"""Kiem thu tich hop tang Device <-> HT4 qua Mosquitto that, voi ACL va tai khoan that.

Kho ban tin la ban gia lap trong bo nho (khong can SQL Server); cac buoc nghiep vu
duoc thay bang ham ghi nhan. Kiem chung: hop dong ban tin, ACL chong gia mao (Bang 6.6),
Last Will, bo dem khi mat ket noi va chong ghi trung khi gui lai (KB4).
Bo qua neu may khong co mosquitto.
"""
import getpass
import json
import os
import shutil
import socket
import subprocess
import threading
import time
import uuid

import pytest

pytestmark = pytest.mark.skipif(shutil.which("mosquitto") is None, reason="cần mosquitto")

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MK_TB, MK_SERVER = "mk-thiet-bi", "mk-server"


class KhoBoNho:
    def __init__(self):
        self.khoa = threading.Lock()
        self.ban_tin, self.lich_su_tb = {}, []
        self.loai = {"GT-01": "CONG_NHAP", "GT-02": "CONG_XUAT", "HH-01": "CAM_TAY",
                     "AGV-01": "AGV", "AGV-02": "AGV"}

    def ghi_moi(self, ma, ma_tb, chu_de, noi_dung):
        with self.khoa:
            if ma in self.ban_tin:
                return False
            self.ban_tin[ma] = "CHO"
            return True

    def danh_dau(self, ma, tt):
        with self.khoa:
            self.ban_tin[ma] = tt

    def loai_thiet_bi(self, ma_tb):
        return self.loai.get(ma_tb)

    def cap_nhat_trang_thai_tb(self, ma_tb, tt):
        with self.khoa:
            self.lich_su_tb.append((ma_tb, tt))

    def ban_tin_cho(self):
        return []

    def trang_thai(self, ma_tb):
        with self.khoa:
            ds = [tt for m, tt in self.lich_su_tb if m == ma_tb]
        return ds[-1] if ds else None


def cho(dieu_kien, giay=15.0):
    het = time.time() + giay
    while time.time() < het:
        if dieu_kien():
            return True
        time.sleep(0.1)
    return False


def _mo_duoc(cong):
    try:
        socket.create_connection(("127.0.0.1", cong), 1).close()
        return True
    except OSError:
        return False


@pytest.fixture(scope="module")
def broker(tmp_path_factory):
    d = tmp_path_factory.mktemp("mqtt")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        cong = s.getsockname()[1]
    passwd = d / "passwd"
    passwd.write_text("")
    subprocess.run(["mosquitto_passwd", "-b", str(passwd), "server", MK_SERVER], check=True)
    for tb in ("GT-01", "GT-02", "HH-01", "AGV-01", "AGV-02"):
        subprocess.run(["mosquitto_passwd", "-b", str(passwd), tb, MK_TB], check=True)
    os.chmod(passwd, 0o600)
    conf = d / "mosquitto.conf"
    nguoi_chay = f"user {getpass.getuser()}\n"   # mosquitto chay bang root se doi sang user khac neu khong khai bao
    conf.write_text(nguoi_chay + f"listener {cong} 127.0.0.1\nallow_anonymous false\npassword_file {passwd}\n"
                    f"acl_file {os.path.join(GOC, 'mosquitto', 'acl')}\n")
    p = subprocess.Popen(["mosquitto", "-c", str(conf)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert cho(lambda: _mo_duoc(cong), 5), "mosquitto không khởi động"
    yield cong
    p.terminate()
    p.wait()


@pytest.fixture(scope="module")
def he_thong(broker):
    import cau_hinh as cfg
    from ht4_thiet_bi.kenh_mqtt import KenhMQTT
    from ht4_thiet_bi.tiep_nhan import BoTiepNhan
    from thiet_bi import AGV, QuanLyThietBi

    cfg.MQTT_HOST, cfg.MQTT_PORT, cfg.MQTT_USER, cfg.MQTT_PASSWORD = "127.0.0.1", broker, "server", MK_SERVER
    AGV.THOI_GIAN_CHAY, AGV.THOI_GIAN_MAT_KET_NOI = 0.5, 9.0

    kho = KhoBoNho()
    nghiep_vu = []   # (loai, ban_tin) da chuyen vao nghiep vu
    xu_ly = {k: (lambda bt, k=k: nghiep_vu.append((k, bt))) for k in ("CONG_NHAP", "CONG_XUAT", "CAM_TAY", "AGV")}
    bo = BoTiepNhan(kho, xu_ly)
    ket_qua = []
    goc = bo.tiep_nhan
    bo.tiep_nhan = lambda c, d: ket_qua.append((c, goc(c, d))) or ket_qua[-1][1]
    kenh = KenhMQTT(bo)
    kenh.bat_dau()
    ql = QuanLyThietBi("127.0.0.1", broker, MK_TB).bat_dau()
    assert cho(lambda: all(kho.trang_thai(m) == "TRUC_TUYEN" for m in ql.thiet_bi)), kho.lich_su_tb
    yield kenh, ql, kho, nghiep_vu, ket_qua
    ql.dung()
    kenh.dung()


def test_cong_nhap_gui_luot_doc_den_nghiep_vu(he_thong):
    _, ql, _, nghiep_vu, _ = he_thong
    from kich_ban import epc
    ql.doc("GT-01", [epc(21), epc(22), epc(23)])
    assert cho(lambda: any(l == "CONG_NHAP" for l, _ in nghiep_vu))
    bt = [b for l, b in nghiep_vu if l == "CONG_NHAP"][-1]
    assert [t.maEPC for t in bt.the] == [epc(21), epc(22), epc(23)]


def test_acl_chan_thiet_bi_gia_mao_thiet_bi_khac(he_thong):
    _, ql, _, nghiep_vu, ket_qua = he_thong
    from kich_ban import epc
    gia_mao = {"v": 1, "maBanTin": str(uuid.uuid4()), "maTB": "GT-02", "thoiDiem": "2026-10-13T10:00:00+07:00",
               "the": [{"maEPC": epc(1)}]}
    # GT-01 dung tai khoan cua minh ghi vao chu de cua GT-02: broker phai chan
    ql.thiet_bi["GT-01"].client.publish("kho/thietbi/GT-02/doc-the", json.dumps(gia_mao), qos=1)
    time.sleep(1.5)
    assert not any(l == "CONG_XUAT" for l, _ in nghiep_vu)
    assert not any(c == "kho/thietbi/GT-02/doc-the" for c, _ in ket_qua)


def test_agv_nhan_lenh_va_bao_hoan_thanh(he_thong):
    kenh, _, _, nghiep_vu, _ = he_thong
    kenh.phat("kho/agv/AGV-02/lenh", {"v": 1, "maBanTin": str(uuid.uuid4()), "maNVu": "NV-261013-001",
                                      "maKien": "KI-2610-00021", "viTriDi": "N-01-01-01",
                                      "viTriDen": "A-02-01-01", "thoiDiem": "2026-10-13T10:00:00+07:00"})
    assert cho(lambda: [b.trangThai for l, b in nghiep_vu if l == "AGV" and b.maTB == "AGV-02"]
               == ["DANG_THUC_HIEN", "HOAN_THANH"], 10)


def test_kb4_mat_ket_noi_last_will_bo_dem_va_chong_trung(he_thong):
    kenh, ql, kho, nghiep_vu, ket_qua = he_thong
    ql.thiet_bi["AGV-01"].loi_lan_toi = True
    kenh.phat("kho/agv/AGV-01/lenh", {"v": 1, "maBanTin": str(uuid.uuid4()), "maNVu": "NV-261013-002",
                                      "maKien": "KI-2610-00022", "viTriDi": "N-01-01-01",
                                      "viTriDen": "A-02-01-02", "thoiDiem": "2026-10-13T10:00:00+07:00"})
    # Broker phat Last Will khi AGV-01 mat ket noi bat thuong
    assert cho(lambda: kho.trang_thai("AGV-01") == "NGOAI_TUYEN", 15), kho.lich_su_tb
    # AGV-01 ket noi lai va gui lai ban tin trong bo dem
    assert cho(lambda: kho.trang_thai("AGV-01") == "TRUC_TUYEN", 15)
    hoan_thanh = lambda: [b for l, b in nghiep_vu if l == "AGV" and b.maTB == "AGV-01" and b.trangThai == "HOAN_THANH"]
    assert cho(lambda: len(hoan_thanh()) == 1, 10)
    time.sleep(1)
    assert len(hoan_thanh()) == 1                                  # nghiep vu chi chay mot lan
    assert sum(1 for c, kq in ket_qua if c == "kho/agv/AGV-01/nhiem-vu" and kq == "TRUNG") == 1
