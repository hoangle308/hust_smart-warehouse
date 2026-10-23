"""REST API cua HT2 - Nhap kho (Bang 6.5)."""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from db import giao_tac, thanh_dict, truy_van
from ht1_danh_muc.phan_quyen import NV_KHO, THU_KHO, nguoi_dung_hien_tai, yeu_cau
from ht2_nhap_kho import dieu_khien as dk

router = APIRouter(tags=["HT2 Nhập kho"])


class DongDon(BaseModel):
    maMH: str
    soLuong: int = Field(gt=0)


class DonDatHangMoi(BaseModel):
    soDDH: str = Field(min_length=1, max_length=20)
    ngayDat: date
    maNCC: str
    dong: list[DongDon] = Field(min_length=1)


class PhieuGiao(BaseModel):
    soDDH: str


class KienMoi(BaseModel):
    maMH: str
    soLuong: int = Field(gt=0)
    maEPC: str = Field(pattern=r"^[0-9A-F]{24}$")


@router.get("/don-dat-hang")
def ds_don(_=Depends(nguoi_dung_hien_tai)):
    with giao_tac() as cur:
        cur.execute("SELECT d.SoDDH, d.NgayDat, d.MaNCC, n.TenNCC FROM kho.DON_DAT_HANG d "
                    "JOIN kho.NHA_CUNG_CAP n ON n.MaNCC = d.MaNCC ORDER BY d.SoDDH")
        don = thanh_dict(cur)
        cur.execute("SELECT SoDDH, MaMH, SoLuongDat FROM kho.DONG_DDH ORDER BY SoDDH, MaMH")
        dong = thanh_dict(cur)
    for d in don:
        d["dong"] = [x for x in dong if x["SoDDH"] == d["SoDDH"]]
    return don


@router.post("/don-dat-hang", status_code=201)
def tao_don(body: DonDatHangMoi, nd=Depends(yeu_cau(THU_KHO))):
    return {"soDDH": dk.tao_don_dat_hang(body.soDDH, body.ngayDat, body.maNCC,
                                         [(x.maMH, x.soLuong) for x in body.dong], nd["maNV"])}


@router.post("/phieu-giao", status_code=201)
def tiep_nhan_phieu_giao(body: PhieuGiao, nd=Depends(yeu_cau(THU_KHO, NV_KHO))):
    return {"soPN": dk.tiep_nhan_phieu_giao(body.soDDH, nd["maNV"])}


@router.get("/phieu-giao/dang-nhan")
def phieu_dang_nhan(_=Depends(nguoi_dung_hien_tai)):
    r = truy_van("SELECT SoPN, SoDDH, NgayNhap FROM kho.PHIEU_NHAP WHERE TrangThai = 'DANG_NHAN'")
    return r[0] if r else None


@router.get("/phieu-giao/{so_pn}/doi-chieu")
def doi_chieu(so_pn: str, _=Depends(nguoi_dung_hien_tai)):
    return dk.ket_qua_doi_chieu(so_pn)


@router.post("/kien", status_code=201)
def khai_bao_kien(body: KienMoi, nd=Depends(yeu_cau(THU_KHO, NV_KHO))):
    return {"maKien": dk.khai_bao_kien(body.maMH, body.soLuong, body.maEPC, nd["maNV"])}


@router.get("/kien")
def ds_kien(trangThai: str | None = None, _=Depends(nguoi_dung_hien_tai)):
    sql = ("SELECT k.MaKien, k.MaEPC, k.MaMH, m.TenMH, k.SoLuong, k.MaViTri, k.TrangThai, k.NgayNhap "
           "FROM kho.KIEN_HANG k JOIN kho.MAT_HANG m ON m.MaMH = k.MaMH")
    if trangThai:
        return truy_van(sql + " WHERE k.TrangThai = ? ORDER BY k.MaKien", trangThai)
    return truy_van(sql + " ORDER BY k.MaKien")


@router.post("/phieu-nhap/{so_pn}/lap")
def lap_phieu_nhap(so_pn: str, nd=Depends(yeu_cau(THU_KHO))):
    return dk.lap_phieu_nhap(so_pn, nd["maNV"])


@router.get("/phieu-nhap")
def ds_phieu_nhap(_=Depends(nguoi_dung_hien_tai)):
    return truy_van("SELECT p.SoPN, p.NgayNhap, p.SoDDH, p.MaNV, p.TrangThai, "
                    "(SELECT COUNT(*) FROM kho.DONG_PHIEU_NHAP d WHERE d.SoPN = p.SoPN) AS SoKien "
                    "FROM kho.PHIEU_NHAP p ORDER BY p.SoPN DESC")
