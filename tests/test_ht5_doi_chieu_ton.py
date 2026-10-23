"""Doi chieu ton so sach (5.3) -- logic cua KB5."""
from ht5_kiem_ke.doi_chieu_ton import KHOP, SAI_VI_TRI, THIEU, doi_chieu_ton


def test_kb5_doc_9_trong_10_kien():
    so_sach = {f"K{i}" for i in range(1, 11)}
    kq = doi_chieu_ton(so_sach, so_sach - {"K10"})
    assert kq["K10"] == THIEU
    assert sum(v == KHOP for v in kq.values()) == 9


def test_kien_cua_khu_khac_doc_duoc_la_sai_vi_tri():
    assert doi_chieu_ton({"K1"}, {"K1", "B7"}) == {"K1": KHOP, "B7": SAI_VI_TRI}
