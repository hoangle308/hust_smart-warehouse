"""HT4 - Dieu phoi van chuyen: 4.1 Giao nhiem vu, 4.2 Theo doi trang thai, 4.3 Ghi nhan hoan thanh.

Nhiem vu duoc tao o 2.4 (cat) va 3.2 (lay) qua tao_nhiem_vu(); vong dieu phoi
giao nhiem vu cho AGV ranh va phat lenh qua MQTT.
"""
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Callable

import cau_hinh as cfg
from db import giao_tac, ma_chung_tu, mot_dong, thanh_dict

log = logging.getLogger(__name__)

DANG_CHAY = ("DA_GIAO", "DANG_THUC_HIEN")


def tao_nhiem_vu(cur, loai: str, ma_kien: str, vi_tri_di: str, vi_tri_den: str) -> str:
    """Ghi mot nhiem vu moi vao D8 (goi tu 2.4 va 3.2, trong giao tac cua ben goi)."""
    ma = ma_chung_tu(cur, "NV", "NHIEM_VU_VC", "MaNVu")
    cur.execute("INSERT INTO kho.NHIEM_VU_VC (MaNVu, LoaiNVu, MaKien, ViTriDi, ViTriDen) VALUES (?,?,?,?,?)",
                ma, loai, ma_kien, vi_tri_di, vi_tri_den)
    return ma


# ---------------- 4.1 Giao nhiem vu
def giao_nhiem_vu(phat: Callable[[str, dict], None]) -> int:
    """Ghep nhiem vu CHO_GIAO voi AGV truc tuyen dang ranh; phat lenh sau khi commit."""
    lenh = []
    with giao_tac() as cur:
        cur.execute("SELECT MaTB FROM kho.THIET_BI t WHERE LoaiTB = 'AGV' AND TrangThai = 'TRUC_TUYEN' "
                    "AND NOT EXISTS (SELECT 1 FROM kho.NHIEM_VU_VC n WHERE n.MaTB = t.MaTB "
                    "AND n.TrangThai IN ('DA_GIAO','DANG_THUC_HIEN')) ORDER BY MaTB")
        agv_ranh = [r[0] for r in cur.fetchall()]
        if not agv_ranh:
            return 0
        cur.execute(f"SELECT TOP ({len(agv_ranh)}) MaNVu, MaKien, ViTriDi, ViTriDen "
                    "FROM kho.NHIEM_VU_VC WITH (UPDLOCK, READPAST) WHERE TrangThai = 'CHO_GIAO' "
                    "ORDER BY TgTao, MaNVu")
        for nv, agv in zip(thanh_dict(cur), agv_ranh):
            cur.execute("UPDATE kho.NHIEM_VU_VC SET TrangThai = 'DA_GIAO', MaTB = ? WHERE MaNVu = ?",
                        agv, nv["MaNVu"])
            lenh.append((agv, nv))
    for agv, nv in lenh:
        phat(f"kho/agv/{agv}/lenh", {
            "v": 1, "maBanTin": str(uuid.uuid4()), "maNVu": nv["MaNVu"], "maKien": nv["MaKien"],
            "viTriDi": nv["ViTriDi"], "viTriDen": nv["ViTriDen"],
            "thoiDiem": datetime.now(timezone.utc).isoformat()})
        log.info("Giao %s cho %s", nv["MaNVu"], agv)
    return len(lenh)


# ---------------- 4.3 Ghi nhan hoan thanh
def _hoan_thanh(cur, nv: dict) -> bool:
    """Cap nhat vi tri kien va dong nhiem vu. Tra False neu da hoan thanh (bat bien nghiep vu)."""
    if nv["TrangThai"] == "HOAN_THANH":
        return False
    cur.execute("UPDATE kho.KIEN_HANG SET MaViTri = ? WHERE MaKien = ?", nv["ViTriDen"], nv["MaKien"])
    if nv["LoaiNVu"] == "CAT":
        cur.execute("UPDATE kho.VI_TRI SET TrangThai = 'SAN_SANG' WHERE MaViTri = ? AND TrangThai = 'DAT_TRUOC'",
                    nv["ViTriDen"])
    cur.execute("UPDATE kho.NHIEM_VU_VC SET TrangThai = 'HOAN_THANH', TgHoanThanh = SYSDATETIME() "
                "WHERE MaNVu = ?", nv["MaNVu"])
    return True


def _doc_nhiem_vu(cur, ma_nvu: str) -> dict:
    cur.execute("SELECT * FROM kho.NHIEM_VU_VC WITH (UPDLOCK) WHERE MaNVu = ?", ma_nvu)
    nv = mot_dong(cur)
    if nv is None:
        raise LookupError(f"Không có nhiệm vụ {ma_nvu}")
    return nv


# ---------------- 4.2 Theo doi trang thai (xu ly ban tin AGV)
def cap_nhat_nhiem_vu(bt) -> None:
    """Xu ly ban tin trang thai nhiem vu tu AGV (hop dong: BanTinNhiemVu)."""
    with giao_tac() as cur:
        nv = _doc_nhiem_vu(cur, bt.maNVu)
        if nv["MaTB"] != bt.maTB:
            raise ValueError(f"{bt.maTB} báo trạng thái cho nhiệm vụ không được giao cho nó")
        if bt.trangThai == "DANG_THUC_HIEN" and nv["TrangThai"] == "DA_GIAO":
            cur.execute("UPDATE kho.NHIEM_VU_VC SET TrangThai = 'DANG_THUC_HIEN' WHERE MaNVu = ?", bt.maNVu)
        elif bt.trangThai == "HOAN_THANH":
            if not _hoan_thanh(cur, nv):
                log.info("%s đã hoàn thành trước đó, bỏ qua", bt.maNVu)
        elif bt.trangThai == "LOI" and nv["TrangThai"] in DANG_CHAY:
            cur.execute("UPDATE kho.NHIEM_VU_VC SET TrangThai = 'LOI' WHERE MaNVu = ?", bt.maNVu)


def xac_nhan_thu_cong(ma_nvu: str, ma_nv: str) -> None:
    """Thu tuc TC4: thu kho xac nhan nhiem vu da duoc nguoi lam thay AGV."""
    with giao_tac(ma_nv) as cur:
        nv = _doc_nhiem_vu(cur, ma_nvu)
        if not _hoan_thanh(cur, nv):
            raise ValueError(f"Nhiệm vụ {ma_nvu} đã hoàn thành")


class VongDieuPhoi(threading.Thread):
    """Chay giao_nhiem_vu theo chu ky; loi tam thoi khong lam dung vong lap."""

    def __init__(self, phat: Callable[[str, dict], None]):
        super().__init__(daemon=True, name="dieu-phoi")
        self._phat = phat
        self._dung = threading.Event()

    def run(self):
        while not self._dung.wait(cfg.CHU_KY_DIEU_PHOI_GIAY):
            try:
                giao_nhiem_vu(self._phat)
            except Exception:
                log.exception("Lỗi vòng điều phối")

    def dung(self):
        self._dung.set()
