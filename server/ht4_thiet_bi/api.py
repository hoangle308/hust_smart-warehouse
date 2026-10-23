"""REST API cua HT4 - Dieu phoi va thiet bi."""
from fastapi import APIRouter, Depends

from db import truy_van
from ht1_danh_muc.phan_quyen import QUAN_TRI, THU_KHO, nguoi_dung_hien_tai, yeu_cau
from ht4_thiet_bi import dieu_phoi

router = APIRouter(tags=["HT4 Điều phối và thiết bị"])


@router.get("/nhiem-vu")
def ds_nhiem_vu(trangThai: str | None = None, _=Depends(nguoi_dung_hien_tai)):
    sql = ("SELECT n.MaNVu, n.LoaiNVu, n.MaKien, k.MaMH, n.ViTriDi, n.ViTriDen, n.MaTB, n.TrangThai, "
           "n.TgTao, n.TgHoanThanh FROM kho.NHIEM_VU_VC n JOIN kho.KIEN_HANG k ON k.MaKien = n.MaKien")
    if trangThai:
        return truy_van(sql + " WHERE n.TrangThai = ? ORDER BY n.MaNVu DESC", trangThai)
    return truy_van(sql + " ORDER BY n.MaNVu DESC")


@router.post("/nhiem-vu/{ma_nvu}/xac-nhan-thu-cong")
def xac_nhan_thu_cong(ma_nvu: str, nd=Depends(yeu_cau(THU_KHO))):
    dieu_phoi.xac_nhan_thu_cong(ma_nvu, nd["maNV"])
    return {"maNVu": ma_nvu, "trangThai": "HOAN_THANH"}


@router.get("/thiet-bi/trang-thai")
def trang_thai_thiet_bi(_=Depends(nguoi_dung_hien_tai)):
    return truy_van("SELECT t.MaTB, t.LoaiTB, t.TrangThai, "
                    "(SELECT MAX(ThoiDiemNhan) FROM kho.BAN_TIN_THIET_BI b WHERE b.MaTB = t.MaTB) AS BanTinCuoi "
                    "FROM kho.THIET_BI t ORDER BY t.MaTB")


@router.get("/ban-tin")
def ban_tin_gan_day(soLuong: int = 50, _=Depends(yeu_cau(QUAN_TRI, THU_KHO))):
    return truy_van("SELECT TOP (?) MaBanTin, MaTB, ChuDe, ThoiDiemNhan, TrangThaiXuLy "
                    "FROM kho.BAN_TIN_THIET_BI ORDER BY ThoiDiemNhan DESC", min(soLuong, 500))
