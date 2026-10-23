"""Xac thuc nguoi dung: bam mat khau PBKDF2 va JWT (RFC 7519) -- Muc 6.3."""
import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt

import cau_hinh as cfg


def bam_mat_khau(mat_khau: str, muoi: str, vong: int = 100_000) -> str:
    h = hashlib.pbkdf2_hmac("sha256", mat_khau.encode(), muoi.encode(), vong).hex()
    return f"pbkdf2_sha256${vong}${muoi}${h}"


def kiem_tra_mat_khau(mat_khau: str, chuoi_bam: str) -> bool:
    try:
        _, vong, muoi, _ = chuoi_bam.split("$")
    except ValueError:
        return False
    return hmac.compare_digest(bam_mat_khau(mat_khau, muoi, int(vong)), chuoi_bam)


def tao_token(ma_nv: str, vai_tro: str, ho_ten: str) -> str:
    het_han = datetime.now(timezone.utc) + timedelta(hours=cfg.JWT_HET_HAN_GIO)
    return jwt.encode({"sub": ma_nv, "vaiTro": vai_tro, "hoTen": ho_ten, "exp": het_han},
                      cfg.JWT_SECRET, algorithm="HS256")


def giai_ma_token(token: str) -> dict:
    """Nem jwt.PyJWTError neu token sai hoac het han."""
    return jwt.decode(token, cfg.JWT_SECRET, algorithms=["HS256"])
