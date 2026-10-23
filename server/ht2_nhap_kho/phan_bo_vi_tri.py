"""Chuc nang 2.4 - Phan bo vi tri cat (P-Spec 2.4). Ham thuan. Mau thu: MT-05, MT-06."""
from cau_hinh import VI_TRI_KHU_CHO


def chon_o(o_trong_uu_tien: list[str], o_trong_du_phong: list[str]) -> tuple[str, bool]:
    """Chon o trong ma nho nhat cua khu uu tien; het thi khu du phong; het nua thi khu cho W.

    Tra ve (ma_vi_tri, co_canh_bao_het_vi_tri).
    """
    if o_trong_uu_tien:
        return min(o_trong_uu_tien), False
    if o_trong_du_phong:
        return min(o_trong_du_phong), False
    return VI_TRI_KHU_CHO, True
