"""Kiem tra quyen theo vai tro (Bang 6.7). Module "Kiem tra quyen" -- mau thu MT-10."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ht1_danh_muc.xac_thuc import giai_ma_token

QUAN_TRI, THU_KHO, NV_KHO, QUAN_LY = "QUAN_TRI", "THU_KHO", "NV_KHO", "QUAN_LY"
MOI_VAI_TRO = (QUAN_TRI, THU_KHO, NV_KHO, QUAN_LY)


class KhongDuQuyen(Exception):
    pass


def kiem_tra_quyen(vai_tro: str, cho_phep: tuple[str, ...]) -> None:
    """Ham thuan: nem KhongDuQuyen neu vai tro khong nam trong danh sach cho phep."""
    if vai_tro not in cho_phep:
        raise KhongDuQuyen(f"Vai trò {vai_tro} không được phép thực hiện thao tác này")


_bearer = HTTPBearer(auto_error=False)


def nguoi_dung_hien_tai(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa đăng nhập")
    try:
        p = giai_ma_token(cred.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn")
    return {"maNV": p["sub"], "vaiTro": p["vaiTro"], "hoTen": p.get("hoTen", "")}


def yeu_cau(*cho_phep: str):
    """Dependency FastAPI: chi cho phep cac vai tro liet ke."""
    def _kiem_tra(nd: dict = Depends(nguoi_dung_hien_tai)) -> dict:
        try:
            kiem_tra_quyen(nd["vaiTro"], cho_phep)
        except KhongDuQuyen as e:
            raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
        return nd
    return _kiem_tra
