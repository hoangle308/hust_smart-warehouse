"""REST API cua HT6 - Bao cao, tra cuu (6.1-6.3). Chi doc; ton kho doc tu view bao_cao.TON_KHO."""
from datetime import date

from fastapi import APIRouter, Depends

from db import giao_tac, thanh_dict, truy_van
from ht1_danh_muc.phan_quyen import QUAN_LY, THU_KHO, nguoi_dung_hien_tai, yeu_cau

router = APIRouter(tags=["HT6 Báo cáo, tra cứu"])


@router.get("/bang-dieu-khien")
def bang_dieu_khien(_=Depends(nguoi_dung_hien_tai)):
    with giao_tac() as cur:
        cur.execute("""SELECT
            (SELECT COUNT(*) FROM kho.KIEN_HANG WHERE TrangThai = 'TRONG_KHO') AS SoKienTrongKho,
            (SELECT COUNT(*) FROM kho.KIEN_HANG WHERE TrangThai = 'KHAI_BAO') AS SoKienChoNhap,
            (SELECT COUNT(*) FROM kho.PHIEU_NHAP WHERE TrangThai = 'DANG_NHAN') AS PhieuNhapDangNhan,
            (SELECT COUNT(*) FROM kho.PHIEU_XUAT WHERE TrangThai = 'DA_LAP') AS PhieuXuatChoXacNhan,
            (SELECT COUNT(*) FROM kho.NHIEM_VU_VC WHERE TrangThai IN ('CHO_GIAO','DA_GIAO','DANG_THUC_HIEN')) AS NhiemVuDangChay,
            (SELECT COUNT(*) FROM kho.NHIEM_VU_VC WHERE TrangThai = 'LOI') AS NhiemVuLoi,
            (SELECT COUNT(*) FROM kho.THIET_BI WHERE TrangThai = 'TRUC_TUYEN') AS ThietBiTrucTuyen,
            (SELECT COUNT(*) FROM kho.THIET_BI) AS TongThietBi,
            (SELECT COUNT(*) FROM kho.SAI_LECH WHERE ThoiDiem > DATEADD(HOUR, -24, SYSDATETIME())) AS SaiLech24h,
            (SELECT COUNT(*) FROM kho.PHIEN_KIEM_KE WHERE TrangThai = 'CHO_DUYET') AS PhienChoDuyet""")
        so_lieu = thanh_dict(cur)[0]
        cur.execute("SELECT TOP 10 LoaiChungTu, SoChungTu, MaEPC, KetQua, ThoiDiem FROM kho.SAI_LECH "
                    "ORDER BY MaSL DESC")
        so_lieu["saiLechGanDay"] = thanh_dict(cur)
    return so_lieu


@router.get("/bao-cao/ton-kho")
def ton_kho(_=Depends(nguoi_dung_hien_tai)):
    return truy_van("SELECT t.MaMH, m.TenMH, m.DonViTinh, t.SoLuongTon, t.SoKien "
                    "FROM bao_cao.TON_KHO t JOIN kho.MAT_HANG m ON m.MaMH = t.MaMH ORDER BY t.MaMH")


@router.get("/bao-cao/nhap-xuat-ton")
def nhap_xuat_ton(tuNgay: date, _=Depends(yeu_cau(THU_KHO, QUAN_LY))):
    """6.1: ky bao cao tu tuNgay den hien tai. Ton dau = ton cuoi - nhap + xuat + that lac trong ky."""
    return truy_van("""
        WITH nhap AS (
            SELECT k.MaMH, SUM(k.SoLuong) AS SL FROM kho.DONG_PHIEU_NHAP dp
            JOIN kho.PHIEU_NHAP p ON p.SoPN = dp.SoPN AND p.TrangThai = 'DA_LAP' AND p.NgayNhap >= ?
            JOIN kho.KIEN_HANG k ON k.MaKien = dp.MaKien GROUP BY k.MaMH),
        xuat AS (
            SELECT d.MaMH, SUM(d.SoLuong) AS SL FROM kho.DONG_PHIEU_XUAT d
            JOIN kho.PHIEU_XUAT p ON p.SoPX = d.SoPX AND p.TrangThai = 'DA_XAC_NHAN' AND p.NgayXuat >= ?
            GROUP BY d.MaMH),
        ton AS (SELECT MaMH, SoLuongTon AS SL FROM bao_cao.TON_KHO)
        SELECT m.MaMH, m.TenMH, m.DonViTinh,
               ISNULL(t.SL,0) - ISNULL(n.SL,0) + ISNULL(x.SL,0) AS TonDau,
               ISNULL(n.SL,0) AS Nhap, ISNULL(x.SL,0) AS Xuat, ISNULL(t.SL,0) AS TonCuoi
        FROM kho.MAT_HANG m LEFT JOIN nhap n ON n.MaMH = m.MaMH
        LEFT JOIN xuat x ON x.MaMH = m.MaMH LEFT JOIN ton t ON t.MaMH = m.MaMH
        WHERE n.SL IS NOT NULL OR x.SL IS NOT NULL OR t.SL IS NOT NULL
        ORDER BY m.MaMH""", tuNgay, tuNgay)


@router.get("/tra-cuu/vi-tri")
def tra_cuu_vi_tri(q: str, _=Depends(nguoi_dung_hien_tai)):
    """6.2: tim kien trong kho theo ma hoac ten mat hang, ma kien, ma EPC."""
    mau = f"%{q}%"
    return truy_van("SELECT k.MaKien, k.MaEPC, k.MaMH, m.TenMH, k.SoLuong, k.MaViTri, k.NgayNhap "
                    "FROM kho.KIEN_HANG k JOIN kho.MAT_HANG m ON m.MaMH = k.MaMH "
                    "WHERE k.TrangThai = 'TRONG_KHO' AND (k.MaMH LIKE ? OR m.TenMH LIKE ? "
                    "OR k.MaKien LIKE ? OR k.MaEPC LIKE ?) ORDER BY k.MaMH, k.NgayNhap", mau, mau, mau, mau)


@router.get("/bao-cao/hieu-suat")
def hieu_suat(_=Depends(yeu_cau(THU_KHO, QUAN_LY))):
    """6.3: hieu suat dieu phoi AGV va muc su dung o ke theo khu."""
    agv = truy_van("""SELECT ISNULL(MaTB, N'(thủ công/chưa giao)') AS MaTB, COUNT(*) AS SoNhiemVu,
                          SUM(CASE WHEN TrangThai = 'HOAN_THANH' THEN 1 ELSE 0 END) AS HoanThanh,
                          AVG(CASE WHEN TrangThai = 'HOAN_THANH'
                                   THEN DATEDIFF(SECOND, TgTao, TgHoanThanh) END) AS ThoiGianTBGiay
                      FROM kho.NHIEM_VU_VC GROUP BY MaTB ORDER BY MaTB""")
    khu = truy_van("""SELECT v.MaKhu, COUNT(*) AS SoO,
                          SUM(CASE WHEN EXISTS (SELECT 1 FROM kho.KIEN_HANG k WHERE k.MaViTri = v.MaViTri
                                AND k.TrangThai = 'TRONG_KHO') THEN 1 ELSE 0 END) AS SoODaDung
                      FROM kho.VI_TRI v WHERE v.MaKhu IN (SELECT MaKhu FROM kho.KHU WHERE MaKhu NOT IN ('N','X','W'))
                      GROUP BY v.MaKhu ORDER BY v.MaKhu""")
    return {"agv": agv, "khu": khu}


@router.get("/bao-cao/bang-ke-chung-tu")
def bang_ke_chung_tu(tuNgay: date, _=Depends(yeu_cau(THU_KHO, QUAN_LY))):
    """Bang ke chung tu gui Ke toan: Ky + {So chung tu + Loai chung tu + Ngay}n (Muc 4.9)."""
    return truy_van("""SELECT SoPN AS SoChungTu, N'Phiếu nhập' AS Loai, NgayNhap AS Ngay FROM kho.PHIEU_NHAP
                       WHERE TrangThai = 'DA_LAP' AND NgayNhap >= ?
                       UNION ALL SELECT SoPX, N'Phiếu xuất', NgayXuat FROM kho.PHIEU_XUAT
                       WHERE TrangThai = 'DA_XAC_NHAN' AND NgayXuat >= ?
                       UNION ALL SELECT MaPhien, N'Biên bản kiểm kê', NgayKK FROM kho.PHIEN_KIEM_KE
                       WHERE TrangThai = 'DONG' AND NgayKK >= ?
                       ORDER BY Ngay""", tuNgay, tuNgay, tuNgay)


@router.get("/sai-lech")
def ds_sai_lech(_=Depends(nguoi_dung_hien_tai)):
    return truy_van("SELECT TOP 200 * FROM kho.SAI_LECH ORDER BY MaSL DESC")
