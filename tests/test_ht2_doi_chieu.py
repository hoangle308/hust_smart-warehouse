"""MT-01..MT-04: module Doi chieu kien (2.3), bang quyet dinh Q1-Q4 (Bang 4.3)."""
from ht2_nhap_kho.doi_chieu import (CHAP_NHAN, NGOAI_DON, THE_CHUA_DANG_KY, VUOT_SO_LUONG, KienDaDoc,
                                    doi_chieu_kien, doi_chieu_luot)

CON_LAI = {"CAP-00003": 300, "RES-00001": 200}


def test_mt01_the_chua_dang_ky():                    # Q1
    assert doi_chieu_kien(None, CON_LAI) == THE_CHUA_DANG_KY


def test_mt02_ngoai_don():                           # Q2
    assert doi_chieu_kien(KienDaDoc("K", "ICS-00001", 50), CON_LAI) == NGOAI_DON


def test_mt03_vuot_so_luong():                       # Q3
    assert doi_chieu_kien(KienDaDoc("K", "CAP-00003", 301), CON_LAI) == VUOT_SO_LUONG


def test_mt04_bien_bang_dung_so_con_lai():           # Q4, truong hop bien
    hop_le, sai, con_lai = doi_chieu_luot([("E1", KienDaDoc("K", "RES-00001", 200))], CON_LAI)
    assert [k.ma_kien for _, k in hop_le] == ["K"] and sai == []
    assert con_lai["RES-00001"] == 0
    assert doi_chieu_kien(KienDaDoc("K", "RES-00001", 200), CON_LAI) == CHAP_NHAN


def test_luot_kb1_kb3_tru_dan_so_con_lai():
    """Du lieu cua KB1 roi KB3: kien thu ba cung mat hang vuot so con lai sau hai kien dau."""
    luot = [("E21", KienDaDoc("K21", "CAP-00003", 100)), ("E22", KienDaDoc("K22", "CAP-00003", 100)),
            ("E23", KienDaDoc("K23", "RES-00001", 200)), ("E24", KienDaDoc("K24", "ICS-00001", 50)),
            ("E25", KienDaDoc("K25", "CAP-00003", 200)), ("E999", None)]
    hop_le, sai, con_lai = doi_chieu_luot(luot, CON_LAI)
    assert [e for e, _ in hop_le] == ["E21", "E22", "E23"]
    assert dict(sai) == {"E24": NGOAI_DON, "E25": VUOT_SO_LUONG, "E999": THE_CHUA_DANG_KY}
    assert con_lai == {"CAP-00003": 100, "RES-00001": 0}
    assert CON_LAI == {"CAP-00003": 300, "RES-00001": 200}   # dau vao khong bi sua
