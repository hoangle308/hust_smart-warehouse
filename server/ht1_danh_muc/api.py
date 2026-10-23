"""REST API cua HT1: dang nhap, danh muc (1.1-1.4), nguoi dung."""
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db import giao_tac, mot_dong, truy_van
from ht1_danh_muc.phan_quyen import (MOI_VAI_TRO, QUAN_TRI, THU_KHO, nguoi_dung_hien_tai,
                                     yeu_cau)
from ht1_danh_muc.xac_thuc import bam_mat_khau, kiem_tra_mat_khau, tao_token

router = APIRouter(tags=["HT1 Danh mục và quản trị"])


class DangNhap(BaseModel):
    tenDangNhap: str
    matKhau: str


@router.post("/auth/dang-nhap")
def dang_nhap(body: DangNhap):
    with giao_tac() as cur:
        cur.execute("SELECT MaNV, HoTen, VaiTro, MatKhauBam, TrangThai FROM kho.NHAN_VIEN "
                    "WHERE TenDangNhap = ?", body.tenDangNhap)
        nv = mot_dong(cur)
    if not nv or nv["TrangThai"] != "HOAT_DONG" or not kiem_tra_mat_khau(body.matKhau, nv["MatKhauBam"]):
        raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")
    return {"token": tao_token(nv["MaNV"], nv["VaiTro"], nv["HoTen"]),
            "maNV": nv["MaNV"], "hoTen": nv["HoTen"], "vaiTro": nv["VaiTro"]}


# ---------------- 1.1 Mat hang
class MatHangMoi(BaseModel):
    maMH: str = Field(pattern=r"^[A-Z]{3}-\d{5}$")
    tenMH: str = Field(min_length=1, max_length=100)
    nhomHang: str = Field(pattern=r"^[A-Z]{3}$")
    donViTinh: str = Field(min_length=1, max_length=20)
    moTa: str | None = None


@router.get("/mat-hang")
def ds_mat_hang(_=Depends(nguoi_dung_hien_tai)):
    return truy_van("SELECT MaMH, TenMH, NhomHang, DonViTinh, MoTa FROM kho.MAT_HANG ORDER BY MaMH")


@router.post("/mat-hang", status_code=201)
def them_mat_hang(body: MatHangMoi, nd=Depends(yeu_cau(THU_KHO))):
    if not body.maMH.startswith(body.nhomHang + "-"):
        raise ValueError("Mã mặt hàng phải bắt đầu bằng nhóm hàng (Bảng 4.6)")
    with giao_tac(nd["maNV"]) as cur:
        cur.execute("INSERT INTO kho.MAT_HANG (MaMH, TenMH, NhomHang, DonViTinh, MoTa) VALUES (?,?,?,?,?)",
                    body.maMH, body.tenMH, body.nhomHang, body.donViTinh, body.moTa)
    return {"maMH": body.maMH}


# ---------------- 1.2 Doi tac
@router.get("/doi-tac")
def ds_doi_tac(_=Depends(nguoi_dung_hien_tai)):
    return {"nhaCungCap": truy_van("SELECT * FROM kho.NHA_CUNG_CAP ORDER BY MaNCC"),
            "khachHang": truy_van("SELECT * FROM kho.KHACH_HANG ORDER BY MaKH")}


# ---------------- 1.3 Khu, vi tri
@router.get("/khu")
def ds_khu(_=Depends(nguoi_dung_hien_tai)):
    return truy_van("SELECT * FROM kho.KHU ORDER BY MaKhu")


@router.get("/vi-tri")
def ds_vi_tri(maKhu: str | None = None, _=Depends(nguoi_dung_hien_tai)):
    sql = ("SELECT v.MaViTri, v.MaKhu, v.TrangThai, k.MaKien, k.MaMH, k.SoLuong "
           "FROM kho.VI_TRI v LEFT JOIN kho.KIEN_HANG k ON k.MaViTri = v.MaViTri "
           "AND k.TrangThai IN ('KHAI_BAO','TRONG_KHO')")
    if maKhu:
        return truy_van(sql + " WHERE v.MaKhu = ? ORDER BY v.MaViTri", maKhu)
    return truy_van(sql + " ORDER BY v.MaViTri")


# ---------------- 1.4 The RFID, thiet bi
class TheMoi(BaseModel):
    maEPC: str = Field(pattern=r"^[0-9A-F]{24}$")


@router.get("/the-rfid")
def ds_the(trangThai: str | None = None, _=Depends(nguoi_dung_hien_tai)):
    if trangThai:
        return truy_van("SELECT * FROM kho.THE_RFID WHERE TrangThai = ? ORDER BY MaEPC", trangThai)
    return truy_van("SELECT * FROM kho.THE_RFID ORDER BY MaEPC")


@router.post("/the-rfid", status_code=201)
def dang_ky_the(body: TheMoi, nd=Depends(yeu_cau(QUAN_TRI))):
    with giao_tac(nd["maNV"]) as cur:
        cur.execute("INSERT INTO kho.THE_RFID (MaEPC) VALUES (?)", body.maEPC)
    return {"maEPC": body.maEPC}


@router.get("/thiet-bi")
def ds_thiet_bi(_=Depends(nguoi_dung_hien_tai)):
    return truy_van("SELECT * FROM kho.THIET_BI ORDER BY MaTB")


# ---------------- Nguoi dung (phat hien so 1 cua ma tran CRUD)
class NguoiDungMoi(BaseModel):
    maNV: str = Field(pattern=r"^NV-\d{4}$")
    hoTen: str
    vaiTro: str
    tenDangNhap: str = Field(min_length=3, max_length=50)
    matKhau: str = Field(min_length=6)


@router.get("/nguoi-dung")
def ds_nguoi_dung(_=Depends(yeu_cau(QUAN_TRI))):
    return truy_van("SELECT MaNV, HoTen, VaiTro, TenDangNhap, TrangThai FROM kho.NHAN_VIEN ORDER BY MaNV")


@router.post("/nguoi-dung", status_code=201)
def them_nguoi_dung(body: NguoiDungMoi, nd=Depends(yeu_cau(QUAN_TRI))):
    if body.vaiTro not in MOI_VAI_TRO:
        raise ValueError("Vai trò không hợp lệ")
    with giao_tac(nd["maNV"]) as cur:
        cur.execute("INSERT INTO kho.NHAN_VIEN (MaNV, HoTen, VaiTro, TenDangNhap, MatKhauBam) VALUES (?,?,?,?,?)",
                    body.maNV, body.hoTen, body.vaiTro, body.tenDangNhap,
                    bam_mat_khau(body.matKhau, secrets.token_hex(8)))
    return {"maNV": body.maNV}
