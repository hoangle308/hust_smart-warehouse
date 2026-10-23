"""Chuc nang 2.3 - Doi chieu don dat hang.

Cai dat P-Spec 2.3 va bang quyet dinh Q1-Q4 (Bang 4.3). Ham thuan, khong truy
cap CSDL: nhan danh sach kien da doc va so luong con phai nhan, tra ket qua.
Mau thu: MT-01..MT-04.
"""
from dataclasses import dataclass

CHAP_NHAN = "CHAP_NHAN"                # Q4
THE_CHUA_DANG_KY = "THE_CHUA_DANG_KY"  # Q1
NGOAI_DON = "NGOAI_DON"                # Q2
VUOT_SO_LUONG = "VUOT_SO_LUONG"        # Q3


@dataclass(frozen=True)
class KienDaDoc:
    ma_kien: str
    ma_mh: str
    so_luong: int


def doi_chieu_kien(kien: KienDaDoc | None, con_lai: dict[str, int]) -> str:
    """Ap bang quyet dinh cho mot kien.

    C1: the da khai bao kien?   C2: mat hang co trong don?
    C3: so luong kien <= so luong con phai nhan?
    """
    if kien is None:                            # C1 = K
        return THE_CHUA_DANG_KY
    if kien.ma_mh not in con_lai:               # C2 = K
        return NGOAI_DON
    if kien.so_luong > con_lai[kien.ma_mh]:     # C3 = K
        return VUOT_SO_LUONG
    return CHAP_NHAN                            # C1, C2, C3 = C


def doi_chieu_luot(luot: list[tuple[str, KienDaDoc | None]], con_lai: dict[str, int]):
    """Vong lap DO WHILE cua P-Spec 2.3 cho mot luot doc cong.

    Tra ve (kien_hop_le, sai_lech, con_lai_moi); con_lai dau vao khong bi sua.
    kien_hop_le: list[(ma_epc, KienDaDoc)];  sai_lech: list[(ma_epc, ket_qua)].
    """
    con_lai = dict(con_lai)
    hop_le, sai_lech = [], []
    for ma_epc, kien in luot:
        kq = doi_chieu_kien(kien, con_lai)
        if kq == CHAP_NHAN:
            hop_le.append((ma_epc, kien))
            con_lai[kien.ma_mh] -= kien.so_luong
        else:
            sai_lech.append((ma_epc, kq))
    return hop_le, sai_lech, con_lai
