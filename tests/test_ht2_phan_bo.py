"""MT-05, MT-06: module Phan bo vi tri (2.4)."""
from ht2_nhap_kho.phan_bo_vi_tri import chon_o


def test_uu_tien_o_ma_nho_nhat():
    assert chon_o(["A-01-02-01", "A-01-01-03"], ["C-01-01-01"]) == ("A-01-01-03", False)


def test_mt05_het_khu_uu_tien_dung_khu_du_phong():
    assert chon_o([], ["C-02-01-01", "C-01-01-02"]) == ("C-01-01-02", False)


def test_mt06_het_ca_hai_dua_ve_khu_cho_va_canh_bao():
    assert chon_o([], []) == ("W-01-01-01", True)
