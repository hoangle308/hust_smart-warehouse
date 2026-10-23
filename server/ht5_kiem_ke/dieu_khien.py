"""HT5 - Module "Dieu khien kiem ke" (Hinh 6.4): 5.1 -> 5.2 -> 5.3 -> 5.4."""
import logging

from db import giao_tac, ma_chung_tu, mot_dong, thanh_dict
from ht5_kiem_ke.doi_chieu_ton import THIEU, doi_chieu_ton

log = logging.getLogger(__name__)


# ---------------- 5.1 Lap phien kiem ke
def mo_phien(ma_khu: str, ma_nv: str) -> str:
    with giao_tac(ma_nv) as cur:
        cur.execute("SELECT MaPhien FROM kho.PHIEN_KIEM_KE WITH (UPDLOCK) WHERE TrangThai = 'MO'")
        r = cur.fetchone()
        if r:
            raise ValueError(f"Phiên {r[0]} đang mở; đối chiếu xong mới lập phiên mới")
        cur.execute("SELECT 1 FROM kho.KHU WHERE MaKhu = ?", ma_khu)
        if cur.fetchone() is None:
            raise LookupError(f"Không có khu {ma_khu}")
        ma = ma_chung_tu(cur, "KK", "PHIEN_KIEM_KE", "MaPhien")
        cur.execute("INSERT INTO kho.PHIEN_KIEM_KE (MaPhien, MaKhu, MaNV, NgayKK) "
                    "VALUES (?, ?, ?, CAST(SYSDATETIME() AS DATE))", ma, ma_khu, ma_nv)
    return ma


# ---------------- 5.2 Ghi nhan doc the kiem ke (bo xu ly cho thiet bi CAM_TAY)
def ghi_nhan_doc_the(bt) -> dict:
    with giao_tac() as cur:
        cur.execute("SELECT TOP 1 MaPhien FROM kho.PHIEN_KIEM_KE WHERE TrangThai = 'MO' ORDER BY MaPhien DESC")
        r = cur.fetchone()
        if r is None:
            raise ValueError("Đầu đọc cầm tay gửi dữ liệu nhưng không có phiên kiểm kê nào đang mở")
        ma_phien, ghi, la = r[0], 0, []
        for ma_epc in dict.fromkeys(t.maEPC for t in bt.the):
            cur.execute("SELECT MaKien FROM kho.KIEN_HANG WHERE MaEPC = ? AND TrangThai = 'TRONG_KHO'", ma_epc)
            k = cur.fetchone()
            if k is None:
                la.append(ma_epc)
                continue
            cur.execute("IF NOT EXISTS (SELECT 1 FROM kho.DONG_KIEM_KE WHERE MaPhien = ? AND MaKien = ?) "
                        "INSERT INTO kho.DONG_KIEM_KE (MaPhien, MaKien, KetQua) VALUES (?, ?, 'KHOP')",
                        ma_phien, k[0], ma_phien, k[0])
            ghi += cur.rowcount if cur.rowcount > 0 else 0
    if la:
        log.warning("Phiên %s: %d thẻ không gắn với kiện nào trong kho: %s", ma_phien, len(la), la)
    return {"maPhien": ma_phien, "ghiNhan": ghi, "theLa": la}


# ---------------- 5.3 Doi chieu ton so sach
def doi_chieu(ma_phien: str, ma_nv: str) -> dict:
    with giao_tac(ma_nv) as cur:
        cur.execute("SELECT MaKhu, TrangThai FROM kho.PHIEN_KIEM_KE WITH (UPDLOCK) WHERE MaPhien = ?", ma_phien)
        p = mot_dong(cur)
        if p is None:
            raise LookupError(f"Không có phiên {ma_phien}")
        if p["TrangThai"] != "MO":
            raise ValueError(f"Phiên {ma_phien} đã đối chiếu")
        cur.execute("SELECT k.MaKien FROM kho.KIEN_HANG k JOIN kho.VI_TRI v ON v.MaViTri = k.MaViTri "
                    "WHERE v.MaKhu = ? AND k.TrangThai = 'TRONG_KHO'", p["MaKhu"])
        so_sach = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT MaKien FROM kho.DONG_KIEM_KE WHERE MaPhien = ?", ma_phien)
        da_doc = {r[0] for r in cur.fetchall()}
        kq = doi_chieu_ton(so_sach, da_doc)
        for ma_kien, ket_qua in kq.items():
            if ma_kien in da_doc:
                cur.execute("UPDATE kho.DONG_KIEM_KE SET KetQua = ? WHERE MaPhien = ? AND MaKien = ?",
                            ket_qua, ma_phien, ma_kien)
            else:
                cur.execute("INSERT INTO kho.DONG_KIEM_KE (MaPhien, MaKien, KetQua) VALUES (?, ?, ?)",
                            ma_phien, ma_kien, ket_qua)
        cur.execute("UPDATE kho.PHIEN_KIEM_KE SET TrangThai = 'CHO_DUYET' WHERE MaPhien = ?", ma_phien)
    tong = {}
    for v in kq.values():
        tong[v] = tong.get(v, 0) + 1
    return {"maPhien": ma_phien, "tongHop": tong}


# ---------------- 5.4 Xu ly chenh lech (thu tuc TC6)
def xu_ly_chenh_lech(ma_phien: str, dieu_chinh: set[str], ma_nv: str) -> dict:
    """dieu_chinh: tap ma kien duoc phe duyet 'Dieu chinh so'; cac dong con lai la 'Dieu tra them'."""
    with giao_tac(ma_nv) as cur:
        cur.execute("SELECT TrangThai FROM kho.PHIEN_KIEM_KE WITH (UPDLOCK) WHERE MaPhien = ?", ma_phien)
        r = cur.fetchone()
        if r is None:
            raise LookupError(f"Không có phiên {ma_phien}")
        if r[0] != "CHO_DUYET":
            raise ValueError(f"Phiên {ma_phien} không ở trạng thái chờ duyệt")
        cur.execute("SELECT MaKien, KetQua FROM kho.DONG_KIEM_KE WHERE MaPhien = ? AND KetQua <> 'KHOP'", ma_phien)
        chenh_lech = dict(cur.fetchall())
        da_dieu_chinh = []
        for ma_kien in dieu_chinh & set(chenh_lech):
            if chenh_lech[ma_kien] == THIEU:
                cur.execute("UPDATE kho.KIEN_HANG SET TrangThai = 'THAT_LAC', MaViTri = NULL WHERE MaKien = ?",
                            ma_kien)
                cur.execute("UPDATE kho.THE_RFID SET TrangThai = 'HONG' WHERE MaEPC = "
                            "(SELECT MaEPC FROM kho.KIEN_HANG WHERE MaKien = ?)", ma_kien)
                da_dieu_chinh.append(ma_kien)
            # SAI_VI_TRI: dau doc chi biet khu, khong biet o; ghi nhan de dieu tra, khong sua tu dong
        cur.execute("UPDATE kho.PHIEN_KIEM_KE SET TrangThai = 'DONG' WHERE MaPhien = ?", ma_phien)
    return {"maPhien": ma_phien, "daDieuChinh": da_dieu_chinh}


def ket_qua(ma_phien: str) -> dict:
    with giao_tac() as cur:
        cur.execute("SELECT * FROM kho.PHIEN_KIEM_KE WHERE MaPhien = ?", ma_phien)
        p = mot_dong(cur)
        if p is None:
            raise LookupError(f"Không có phiên {ma_phien}")
        cur.execute("SELECT d.MaKien, k.MaEPC, k.MaMH, k.MaViTri, k.TrangThai, d.KetQua FROM kho.DONG_KIEM_KE d "
                    "JOIN kho.KIEN_HANG k ON k.MaKien = d.MaKien WHERE d.MaPhien = ? ORDER BY d.KetQua, d.MaKien",
                    ma_phien)
        p["dong"] = thanh_dict(cur)
    return p
