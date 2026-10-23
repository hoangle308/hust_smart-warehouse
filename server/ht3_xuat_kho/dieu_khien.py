"""HT3 - Module "Dieu khien xuat kho" (Hinh 6.2): 3.1, 3.2 + 3.3, luot doc cong xuat (3.4)."""
import logging

import cau_hinh as cfg
from db import giao_tac, ma_chung_tu, mot_dong, thanh_dict
from ht3_xuat_kho.chon_kien import KhongDuHang, KienTon, chon_kien_fifo
from ht4_thiet_bi.dieu_phoi import tao_nhiem_vu

log = logging.getLogger(__name__)

# Kien con kha dung: trong kho va chua nam tren phieu xuat dang mo
_SQL_KIEN_KHA_DUNG = """
    SELECT k.MaKien, k.SoLuong, k.NgayNhap, k.MaViTri FROM kho.KIEN_HANG k
    WHERE k.MaMH = ? AND k.TrangThai = 'TRONG_KHO'
      AND NOT EXISTS (SELECT 1 FROM kho.DONG_PHIEU_XUAT d JOIN kho.PHIEU_XUAT p ON p.SoPX = d.SoPX
                      WHERE d.MaKien = k.MaKien AND p.TrangThai = 'DA_LAP')"""


# ---------------- 3.1 Tiep nhan yeu cau xuat
def tao_yeu_cau(ma_kh: str, dong: list[tuple[str, int]], ma_nv: str) -> str:
    with giao_tac(ma_nv) as cur:
        for ma_mh, sl in dong:   # kiem tra ton kha dung truoc khi nhan
            cur.execute(_SQL_KIEN_KHA_DUNG, ma_mh)
            ton = sum(r[1] for r in cur.fetchall())
            if ton < sl:
                raise KhongDuHang(f"{ma_mh}: tồn khả dụng {ton}, yêu cầu {sl}")
        so_yc = ma_chung_tu(cur, "YC", "YEU_CAU_XUAT", "SoYC")
        cur.execute("INSERT INTO kho.YEU_CAU_XUAT (SoYC, NgayYC, MaKH) VALUES (?, CAST(SYSDATETIME() AS DATE), ?)",
                    so_yc, ma_kh)
        for ma_mh, sl in dong:
            cur.execute("INSERT INTO kho.DONG_YC_XUAT (SoYC, MaMH, SoLuongYC) VALUES (?,?,?)", so_yc, ma_mh, sl)
    return so_yc


# ---------------- 3.2 Chon kien va vi tri lay + 3.3 Lap phieu xuat
def lap_phieu_xuat(so_yc: str, ma_nv: str) -> dict:
    with giao_tac(ma_nv) as cur:
        cur.execute("SELECT 1 FROM kho.PHIEU_XUAT WHERE SoYC = ? AND TrangThai <> 'HUY'", so_yc)
        if cur.fetchone():
            raise ValueError(f"Yêu cầu {so_yc} đã có phiếu xuất")
        cur.execute("SELECT MaMH, SoLuongYC FROM kho.DONG_YC_XUAT WHERE SoYC = ?", so_yc)
        dong_yc = cur.fetchall()
        if not dong_yc:
            raise LookupError(f"Không có yêu cầu xuất {so_yc}")

        chon = []   # (KienTon, ma_mh, vi_tri)
        for ma_mh, sl in dong_yc:
            cur.execute(_SQL_KIEN_KHA_DUNG + " ORDER BY k.NgayNhap", ma_mh)
            hang = cur.fetchall()
            vi_tri = {r[0]: r[3] for r in hang}
            for k in chon_kien_fifo([KienTon(r[0], r[1], r[2]) for r in hang], sl):
                chon.append((k, ma_mh, vi_tri[k.ma_kien]))

        so_px = ma_chung_tu(cur, "PX", "PHIEU_XUAT", "SoPX")
        cur.execute("INSERT INTO kho.PHIEU_XUAT (SoPX, NgayXuat, SoYC, MaNV) VALUES (?, SYSDATETIME(), ?, ?)",
                    so_px, so_yc, ma_nv)
        for k, ma_mh, vt in chon:
            cur.execute("INSERT INTO kho.DONG_PHIEU_XUAT (SoPX, MaKien, MaMH, SoLuong) VALUES (?,?,?,?)",
                        so_px, k.ma_kien, ma_mh, k.so_luong)
            tao_nhiem_vu(cur, "LAY", k.ma_kien, vt, cfg.VI_TRI_CUA_XUAT)   # Yeu cau lay -> D8
    return {"soPX": so_px, "kien": [{"maKien": k.ma_kien, "maMH": m, "soLuong": k.so_luong, "maViTri": v}
                                    for k, m, v in chon]}


# ---------------- 3.4 Xac nhan doc the xuat
def xac_nhan_luot_doc_xuat(bt) -> dict:
    """Bo xu ly cho thiet bi CONG_XUAT."""
    with giao_tac() as cur:
        cur.execute("SELECT TOP 1 SoPX, SoYC FROM kho.PHIEU_XUAT WITH (UPDLOCK) WHERE TrangThai = 'DA_LAP' "
                    "ORDER BY NgayXuat")
        px = mot_dong(cur)
        if px is None:
            raise ValueError("Có hàng qua cổng xuất nhưng không có phiếu xuất nào đang mở")
        so_px, xac_nhan, sai = px["SoPX"], 0, 0
        for ma_epc in dict.fromkeys(t.maEPC for t in bt.the):
            cur.execute("SELECT k.MaKien, k.TrangThai FROM kho.DONG_PHIEU_XUAT d "
                        "JOIN kho.KIEN_HANG k ON k.MaKien = d.MaKien WHERE d.SoPX = ? AND k.MaEPC = ?",
                        so_px, ma_epc)
            r = cur.fetchone()
            if r and r[1] == "TRONG_KHO":
                cur.execute("UPDATE kho.KIEN_HANG SET TrangThai = 'DA_XUAT', MaViTri = ? WHERE MaKien = ?",
                            cfg.VI_TRI_CUA_XUAT, r[0])
                cur.execute("UPDATE kho.THE_RFID SET TrangThai = 'CHUA_DUNG' WHERE MaEPC = ?", ma_epc)  # TC3
                cur.execute("UPDATE kho.NHIEM_VU_VC SET TrangThai = 'HOAN_THANH', TgHoanThanh = SYSDATETIME() "
                            "WHERE MaKien = ? AND LoaiNVu = 'LAY' AND TrangThai = 'CHO_GIAO'", r[0])
                xac_nhan += 1
            elif r is None:
                cur.execute("SELECT 1 FROM kho.SAI_LECH WHERE SoChungTu = ? AND MaEPC = ?", so_px, ma_epc)
                if cur.fetchone() is None:
                    cur.execute("INSERT INTO kho.SAI_LECH (LoaiChungTu, SoChungTu, MaEPC, KetQua, MaBanTin) "
                                "VALUES ('PX', ?, ?, 'NGOAI_PHIEU', ?)", so_px, ma_epc, str(bt.maBanTin))
                    sai += 1
        cur.execute("SELECT COUNT(*) FROM kho.DONG_PHIEU_XUAT d JOIN kho.KIEN_HANG k ON k.MaKien = d.MaKien "
                    "WHERE d.SoPX = ? AND k.TrangThai <> 'DA_XUAT'", so_px)
        hoan_tat = cur.fetchone()[0] == 0
        if hoan_tat:
            cur.execute("UPDATE kho.PHIEU_XUAT SET TrangThai = 'DA_XAC_NHAN' WHERE SoPX = ?", so_px)
            log.info("Phiếu %s đã xác nhận xuất kho đủ", so_px)
    return {"soPX": so_px, "xacNhan": xac_nhan, "saiLech": sai, "hoanTat": hoan_tat}


def ds_phieu_xuat() -> list[dict]:
    with giao_tac() as cur:
        cur.execute("SELECT p.SoPX, p.NgayXuat, p.SoYC, y.MaKH, p.TrangThai FROM kho.PHIEU_XUAT p "
                    "JOIN kho.YEU_CAU_XUAT y ON y.SoYC = p.SoYC ORDER BY p.SoPX DESC")
        phieu = thanh_dict(cur)
        cur.execute("SELECT d.SoPX, d.MaKien, k.MaEPC, d.MaMH, d.SoLuong, k.MaViTri, k.TrangThai "
                    "FROM kho.DONG_PHIEU_XUAT d JOIN kho.KIEN_HANG k ON k.MaKien = d.MaKien")
        dong = thanh_dict(cur)
    for p in phieu:
        p["dong"] = [d for d in dong if d["SoPX"] == p["SoPX"]]
    return phieu
