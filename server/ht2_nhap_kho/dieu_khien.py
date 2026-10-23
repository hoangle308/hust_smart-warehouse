"""HT2 - Module "Dieu khien nhap kho" (Hinh 6.1).

Ba loai giao tac: 2.1 tiep nhan phieu giao, 2.2 khai bao kien, luot doc cong
nhap (2.3 -> 2.4 -> ghi D6/D8); them 2.5 lap phieu nhap do thu kho kich hoat.
Logic quyet dinh nam o doi_chieu.py va phan_bo_vi_tri.py (ham thuan).
"""
import logging

import cau_hinh as cfg
from db import giao_tac, ma_chung_tu, ma_kien, mot_dong, thanh_dict
from ht2_nhap_kho.doi_chieu import KienDaDoc, doi_chieu_luot
from ht2_nhap_kho.phan_bo_vi_tri import chon_o
from ht4_thiet_bi.dieu_phoi import tao_nhiem_vu

log = logging.getLogger(__name__)


# ---------------- 2.1 Tiep nhan don, phieu giao
def tao_don_dat_hang(so_ddh: str, ngay_dat, ma_ncc: str, dong: list[tuple[str, int]], ma_nv: str) -> str:
    """Luu ban sao don dat hang do Phong Mua hang gui sang (gia dinh 5, Muc 4.16)."""
    with giao_tac(ma_nv) as cur:
        cur.execute("INSERT INTO kho.DON_DAT_HANG (SoDDH, NgayDat, MaNCC) VALUES (?,?,?)", so_ddh, ngay_dat, ma_ncc)
        for ma_mh, sl in dong:
            cur.execute("INSERT INTO kho.DONG_DDH (SoDDH, MaMH, SoLuongDat) VALUES (?,?,?)", so_ddh, ma_mh, sl)
    return so_ddh


def tiep_nhan_phieu_giao(so_ddh: str, ma_nv: str) -> str:
    """Mo phieu nhap trang thai DANG_NHAN cho lo hang dang toi cong; moi thoi diem mot phieu."""
    with giao_tac(ma_nv) as cur:
        cur.execute("SELECT SoPN FROM kho.PHIEU_NHAP WITH (UPDLOCK) WHERE TrangThai = 'DANG_NHAN'")
        dang_mo = cur.fetchone()
        if dang_mo:
            raise ValueError(f"Phiếu {dang_mo[0]} đang nhận hàng; hãy lập phiếu nhập trước khi nhận lô mới")
        cur.execute("SELECT 1 FROM kho.DON_DAT_HANG WHERE SoDDH = ?", so_ddh)
        if cur.fetchone() is None:
            raise LookupError(f"Không có đơn đặt hàng {so_ddh}")
        so_pn = ma_chung_tu(cur, "PN", "PHIEU_NHAP", "SoPN")
        cur.execute("INSERT INTO kho.PHIEU_NHAP (SoPN, NgayNhap, SoDDH, MaNV) VALUES (?, SYSDATETIME(), ?, ?)",
                    so_pn, so_ddh, ma_nv)
    return so_pn


# ---------------- 2.2 Khai bao kien (thu tuc TC1)
def khai_bao_kien(ma_mh: str, so_luong: int, ma_epc: str, ma_nv: str) -> str:
    with giao_tac(ma_nv) as cur:
        cur.execute("SELECT TrangThai FROM kho.THE_RFID WITH (UPDLOCK) WHERE MaEPC = ?", ma_epc)
        the = cur.fetchone()
        if the is None:
            raise LookupError("Thẻ chưa được đăng ký trong danh mục (chức năng 1.4)")
        if the[0] != "CHUA_DUNG":
            raise ValueError(f"Thẻ đang ở trạng thái {the[0]}, không gắn được cho kiện mới")
        mk = ma_kien(cur)
        cur.execute("INSERT INTO kho.KIEN_HANG (MaKien, MaEPC, MaMH, SoLuong) VALUES (?,?,?,?)",
                    mk, ma_epc, ma_mh, so_luong)
        cur.execute("UPDATE kho.THE_RFID SET TrangThai = 'DANG_DUNG' WHERE MaEPC = ?", ma_epc)
    return mk


# ---------------- Luot doc cong nhap: 2.3 -> 2.4
def _con_lai(cur, so_ddh: str) -> dict[str, int]:
    """So luong con phai nhan theo mat hang = dat - da chap nhan tren moi phieu nhap cua don."""
    cur.execute("""
        SELECT d.MaMH, d.SoLuongDat - ISNULL((
            SELECT SUM(k.SoLuong) FROM kho.DONG_PHIEU_NHAP dp
            JOIN kho.PHIEU_NHAP p ON p.SoPN = dp.SoPN
            JOIN kho.KIEN_HANG k ON k.MaKien = dp.MaKien
            WHERE p.SoDDH = d.SoDDH AND k.MaMH = d.MaMH), 0) AS ConLai
        FROM kho.DONG_DDH d WHERE d.SoDDH = ?""", so_ddh)
    return {r[0]: r[1] for r in cur.fetchall()}


def _o_trong(cur, ds_khu: list[str]) -> list[str]:
    if not ds_khu:
        return []
    dau_hoi = ",".join("?" * len(ds_khu))
    cur.execute(f"""
        SELECT v.MaViTri FROM kho.VI_TRI v
        WHERE v.MaKhu IN ({dau_hoi}) AND v.TrangThai = 'SAN_SANG'
          AND NOT EXISTS (SELECT 1 FROM kho.KIEN_HANG k WHERE k.MaViTri = v.MaViTri
                          AND k.TrangThai IN ('KHAI_BAO','TRONG_KHO'))
          AND NOT EXISTS (SELECT 1 FROM kho.NHIEM_VU_VC n WHERE n.ViTriDen = v.MaViTri
                          AND n.TrangThai NOT IN ('HOAN_THANH','LOI'))""", *ds_khu)
    return [r[0] for r in cur.fetchall()]


def _phan_bo_va_tao_nhiem_vu(cur, kien: KienDaDoc) -> str:
    """Chuc nang 2.4: chon o (ham thuan), dat truoc o, ghi Yeu cau cat vao D8."""
    cur.execute("SELECT k.MaKhu FROM kho.KHU k JOIN kho.MAT_HANG m ON m.NhomHang = k.NhomHangUuTien "
                "WHERE m.MaMH = ?", kien.ma_mh)
    khu_uu_tien = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT MaKhu FROM kho.KHU WHERE LaKhuDuPhong = 1")
    khu_du_phong = [r[0] for r in cur.fetchall()]
    o, canh_bao = chon_o(_o_trong(cur, khu_uu_tien), _o_trong(cur, khu_du_phong))
    if canh_bao:
        log.warning("Hết vị trí cho %s, đưa về khu chờ", kien.ma_kien)
    else:
        cur.execute("UPDATE kho.VI_TRI SET TrangThai = 'DAT_TRUOC' WHERE MaViTri = ?", o)
    return tao_nhiem_vu(cur, "CAT", kien.ma_kien, cfg.VI_TRI_CUA_NHAP, o)


def xu_ly_luot_doc_cong(bt) -> dict:
    """Bo xu ly cho thiet bi CONG_NHAP (ban tin BanTinDocThe)."""
    with giao_tac() as cur:
        cur.execute("SELECT TOP 1 SoPN, SoDDH FROM kho.PHIEU_NHAP WITH (UPDLOCK) "
                    "WHERE TrangThai = 'DANG_NHAN' ORDER BY NgayNhap DESC")
        pn = mot_dong(cur)
        if pn is None:
            raise ValueError("Có hàng qua cổng nhập nhưng chưa tiếp nhận phiếu giao nào")
        so_pn = pn["SoPN"]

        luot = []
        for ma_epc in dict.fromkeys(t.maEPC for t in bt.the):   # bo the doc lap trong cung luot
            # The da xu ly o luot truoc cua phieu nay (doc lai khi kien dung lau truoc cong)
            cur.execute("SELECT 1 FROM kho.DONG_PHIEU_NHAP dp JOIN kho.KIEN_HANG k ON k.MaKien = dp.MaKien "
                        "WHERE dp.SoPN = ? AND k.MaEPC = ? "
                        "UNION SELECT 1 FROM kho.SAI_LECH WHERE SoChungTu = ? AND MaEPC = ?",
                        so_pn, ma_epc, so_pn, ma_epc)
            if cur.fetchone():
                continue
            cur.execute("SELECT MaKien, MaMH, SoLuong FROM kho.KIEN_HANG "
                        "WHERE MaEPC = ? AND TrangThai = 'KHAI_BAO'", ma_epc)
            r = cur.fetchone()
            luot.append((ma_epc, KienDaDoc(r[0], r[1], r[2]) if r else None))

        hop_le, sai_lech, _ = doi_chieu_luot(luot, _con_lai(cur, pn["SoDDH"]))

        for _, kien in hop_le:
            cur.execute("INSERT INTO kho.DONG_PHIEU_NHAP (SoPN, MaKien) VALUES (?, ?)", so_pn, kien.ma_kien)
            cur.execute("UPDATE kho.KIEN_HANG SET MaViTri = ? WHERE MaKien = ?", cfg.VI_TRI_CUA_NHAP, kien.ma_kien)
            _phan_bo_va_tao_nhiem_vu(cur, kien)
        for ma_epc, kq in sai_lech:
            cur.execute("INSERT INTO kho.SAI_LECH (LoaiChungTu, SoChungTu, MaEPC, KetQua, MaBanTin) "
                        "VALUES ('PN', ?, ?, ?, ?)", so_pn, ma_epc, kq, str(bt.maBanTin))
    if sai_lech:
        # Thong bao sai lech gui Phong Mua hang: o ban cai dat nay hien tren Web app
        log.warning("Thông báo sai lệch %s: %s", so_pn, sai_lech)
    return {"soPN": so_pn, "chapNhan": len(hop_le), "saiLech": len(sai_lech)}


# ---------------- Ket qua doi chieu (doc)
def ket_qua_doi_chieu(so_pn: str) -> dict:
    with giao_tac() as cur:
        cur.execute("SELECT * FROM kho.PHIEU_NHAP WHERE SoPN = ?", so_pn)
        pn = mot_dong(cur)
        if pn is None:
            raise LookupError(f"Không có phiếu nhập {so_pn}")
        cur.execute("SELECT k.MaKien, k.MaEPC, k.MaMH, m.TenMH, k.SoLuong, k.MaViTri, k.TrangThai "
                    "FROM kho.DONG_PHIEU_NHAP dp JOIN kho.KIEN_HANG k ON k.MaKien = dp.MaKien "
                    "JOIN kho.MAT_HANG m ON m.MaMH = k.MaMH WHERE dp.SoPN = ? ORDER BY k.MaKien", so_pn)
        chap_nhan = thanh_dict(cur)
        cur.execute("SELECT MaEPC, KetQua, ThoiDiem FROM kho.SAI_LECH WHERE LoaiChungTu = 'PN' AND SoChungTu = ? "
                    "ORDER BY MaSL", so_pn)
        sai_lech = thanh_dict(cur)
        con_lai = _con_lai(cur, pn["SoDDH"])
    return {"phieu": pn, "chapNhan": chap_nhan, "saiLech": sai_lech,
            "conLai": [{"MaMH": k, "ConLai": v} for k, v in con_lai.items()]}


# ---------------- 2.5 Lap phieu nhap
def lap_phieu_nhap(so_pn: str, ma_nv: str) -> dict:
    with giao_tac(ma_nv) as cur:
        cur.execute("SELECT TrangThai FROM kho.PHIEU_NHAP WITH (UPDLOCK) WHERE SoPN = ?", so_pn)
        r = cur.fetchone()
        if r is None:
            raise LookupError(f"Không có phiếu nhập {so_pn}")
        if r[0] != "DANG_NHAN":
            raise ValueError(f"Phiếu {so_pn} đã lập")
        cur.execute("SELECT COUNT(*) FROM kho.DONG_PHIEU_NHAP WHERE SoPN = ?", so_pn)
        if cur.fetchone()[0] == 0:
            raise ValueError("Chưa có kiện nào được chấp nhận, không lập được phiếu nhập")
        cur.execute("UPDATE kho.KIEN_HANG SET TrangThai = 'TRONG_KHO', NgayNhap = SYSDATETIME() "
                    "WHERE TrangThai = 'KHAI_BAO' AND MaKien IN "
                    "(SELECT MaKien FROM kho.DONG_PHIEU_NHAP WHERE SoPN = ?)", so_pn)
        cur.execute("UPDATE kho.PHIEU_NHAP SET TrangThai = 'DA_LAP', NgayNhap = SYSDATETIME(), MaNV = ? "
                    "WHERE SoPN = ?", ma_nv, so_pn)
        # Bien ban giao nhan = So phieu giao + So phieu nhap + {Ma mat hang + So luong nhan}n (Muc 4.9)
        cur.execute("SELECT k.MaMH, m.TenMH, COUNT(*) AS SoKien, SUM(k.SoLuong) AS SoLuongNhan "
                    "FROM kho.DONG_PHIEU_NHAP dp JOIN kho.KIEN_HANG k ON k.MaKien = dp.MaKien "
                    "JOIN kho.MAT_HANG m ON m.MaMH = k.MaMH WHERE dp.SoPN = ? GROUP BY k.MaMH, m.TenMH",
                    so_pn)
        dong = thanh_dict(cur)
        cur.execute("SELECT p.SoPN, p.SoDDH, p.NgayNhap, d.MaNCC, n.TenNCC FROM kho.PHIEU_NHAP p "
                    "JOIN kho.DON_DAT_HANG d ON d.SoDDH = p.SoDDH JOIN kho.NHA_CUNG_CAP n ON n.MaNCC = d.MaNCC "
                    "WHERE p.SoPN = ?", so_pn)
        dau = mot_dong(cur)
    return {"bienBan": dau, "dong": dong}
