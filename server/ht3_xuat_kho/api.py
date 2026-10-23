"""REST API cua HT3 - Xuat kho (Bang 6.5)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from db import giao_tac, thanh_dict
from ht1_danh_muc.phan_quyen import THU_KHO, nguoi_dung_hien_tai, yeu_cau
from ht3_xuat_kho import dieu_khien as dk

router = APIRouter(tags=["HT3 Xuất kho"])


class DongYeuCau(BaseModel):
    maMH: str
    soLuong: int = Field(gt=0)


class YeuCauXuat(BaseModel):
    maKH: str
    dong: list[DongYeuCau] = Field(min_length=1)


@router.post("/yeu-cau-xuat", status_code=201)
def tao_yeu_cau(body: YeuCauXuat, nd=Depends(yeu_cau(THU_KHO))):
    return {"soYC": dk.tao_yeu_cau(body.maKH, [(d.maMH, d.soLuong) for d in body.dong], nd["maNV"])}


@router.get("/yeu-cau-xuat")
def ds_yeu_cau(_=Depends(nguoi_dung_hien_tai)):
    with giao_tac() as cur:
        cur.execute("SELECT y.SoYC, y.NgayYC, y.MaKH, k.TenKH, "
                    "(SELECT TOP 1 p.SoPX FROM kho.PHIEU_XUAT p WHERE p.SoYC = y.SoYC AND p.TrangThai <> 'HUY') AS SoPX "
                    "FROM kho.YEU_CAU_XUAT y JOIN kho.KHACH_HANG k ON k.MaKH = y.MaKH ORDER BY y.SoYC DESC")
        yc = thanh_dict(cur)
        cur.execute("SELECT SoYC, MaMH, SoLuongYC FROM kho.DONG_YC_XUAT")
        dong = thanh_dict(cur)
    for y in yc:
        y["dong"] = [d for d in dong if d["SoYC"] == y["SoYC"]]
    return yc


@router.post("/yeu-cau-xuat/{so_yc}/lap-phieu", status_code=201)
def lap_phieu(so_yc: str, nd=Depends(yeu_cau(THU_KHO))):
    return dk.lap_phieu_xuat(so_yc, nd["maNV"])


@router.get("/phieu-xuat")
def ds_phieu_xuat(_=Depends(nguoi_dung_hien_tai)):
    return dk.ds_phieu_xuat()
