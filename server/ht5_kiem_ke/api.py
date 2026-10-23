"""REST API cua HT5 - Kiem ke (Bang 6.5)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from db import truy_van
from ht1_danh_muc.phan_quyen import QUAN_LY, THU_KHO, nguoi_dung_hien_tai, yeu_cau
from ht5_kiem_ke import dieu_khien as dk

router = APIRouter(tags=["HT5 Kiểm kê"])


class PhienMoi(BaseModel):
    maKhu: str


class QuyetDinh(BaseModel):
    maKien: str
    dieuChinh: bool


class XuLy(BaseModel):
    quyetDinh: list[QuyetDinh] = []


@router.post("/kiem-ke", status_code=201)
def mo_phien(body: PhienMoi, nd=Depends(yeu_cau(THU_KHO))):
    return {"maPhien": dk.mo_phien(body.maKhu, nd["maNV"])}


@router.get("/kiem-ke")
def ds_phien(_=Depends(nguoi_dung_hien_tai)):
    return truy_van("SELECT p.*, (SELECT COUNT(*) FROM kho.DONG_KIEM_KE d WHERE d.MaPhien = p.MaPhien) AS SoDong "
                    "FROM kho.PHIEN_KIEM_KE p ORDER BY p.MaPhien DESC")


@router.get("/kiem-ke/{ma_phien}/ket-qua")
def ket_qua(ma_phien: str, _=Depends(nguoi_dung_hien_tai)):
    return dk.ket_qua(ma_phien)


@router.post("/kiem-ke/{ma_phien}/doi-chieu")
def doi_chieu(ma_phien: str, nd=Depends(yeu_cau(THU_KHO))):
    return dk.doi_chieu(ma_phien, nd["maNV"])


@router.post("/kiem-ke/{ma_phien}/xu-ly")
def xu_ly(ma_phien: str, body: XuLy, nd=Depends(yeu_cau(QUAN_LY))):
    return dk.xu_ly_chenh_lech(ma_phien, {q.maKien for q in body.quyetDinh if q.dieuChinh}, nd["maNV"])
