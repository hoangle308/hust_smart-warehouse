"""MT-09: module Chon kien FIFO (3.2)."""
from datetime import datetime

import pytest

from ht3_xuat_kho.chon_kien import KhongDuHang, KienTon, chon_kien_fifo

D = datetime


def test_mt09_chon_kien_nhap_truoc():
    ds = [KienTon("MOI", 100, D(2026, 10, 1)), KienTon("CU", 100, D(2026, 9, 1))]
    assert [k.ma_kien for k in chon_kien_fifo(ds, 80)] == ["CU"]


def test_xuat_nguyen_kien_kb6():
    """KB6: yeu cau 150 voi kien 100 -> chon 2 kien cu nhat (xuat nguyen kien, gia dinh 1)."""
    ds = [KienTon(f"K{i}", 100, D(2026, 9, i)) for i in (5, 2, 4, 1, 3)]
    assert [k.ma_kien for k in chon_kien_fifo(ds, 150)] == ["K1", "K2"]


def test_khong_du_hang():
    with pytest.raises(KhongDuHang):
        chon_kien_fifo([KienTon("K", 100, D(2026, 9, 1))], 101)
