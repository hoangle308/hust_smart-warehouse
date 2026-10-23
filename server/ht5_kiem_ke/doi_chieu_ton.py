"""Chuc nang 5.3 - Doi chieu ton so sach. Ham thuan (mau thu cua KB5).

so_sach: kien TRONG_KHO co vi tri thuoc khu dang kiem ke.
da_doc : kien doc duoc khi quet khu do (kien da biet, dang TRONG_KHO).
  doc duoc va co trong so sach        -> KHOP
  co trong so sach, khong doc duoc    -> THIEU
  doc duoc trong khu nhung so sach ghi o noi khac -> SAI_VI_TRI
The doc duoc nhung khong gan voi kien nao khong ghi duoc vao DONG_KIEM_KE
(khoa ngoai MaKien) va duoc bao rieng.
"""
KHOP, THIEU, SAI_VI_TRI = "KHOP", "THIEU", "SAI_VI_TRI"


def doi_chieu_ton(so_sach: set[str], da_doc: set[str]) -> dict[str, str]:
    ket_qua = {k: (KHOP if k in so_sach else SAI_VI_TRI) for k in da_doc}
    ket_qua.update({k: THIEU for k in so_sach - da_doc})
    return ket_qua
