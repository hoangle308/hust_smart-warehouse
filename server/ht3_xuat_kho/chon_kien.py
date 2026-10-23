"""Chuc nang 3.2 - Chon kien theo nguyen tac nhap truoc, xuat truoc (FIFO). Ham thuan. Mau thu MT-09.

Gia dinh 1 (Muc 4.16): xuat nguyen kien, nen tong so luong chon co the lon hon so yeu cau.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KienTon:
    ma_kien: str
    so_luong: int
    ngay_nhap: datetime


class KhongDuHang(ValueError):
    pass


def chon_kien_fifo(ds_kien: list[KienTon], so_luong_can: int) -> list[KienTon]:
    if so_luong_can <= 0:
        raise ValueError("Số lượng yêu cầu phải dương")
    da_chon, tong = [], 0
    for k in sorted(ds_kien, key=lambda k: (k.ngay_nhap, k.ma_kien)):
        if tong >= so_luong_can:
            break
        da_chon.append(k)
        tong += k.so_luong
    if tong < so_luong_can:
        raise KhongDuHang(f"Tồn khả dụng {tong} nhỏ hơn số lượng yêu cầu {so_luong_can}")
    return da_chon
