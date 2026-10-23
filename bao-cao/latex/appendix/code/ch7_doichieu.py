def doi_chieu_kien(kien: KienDaDoc | None, con_lai: dict[str, int]) -> str:
    if kien is None:                            # C1 = K
        return THE_CHUA_DANG_KY                 # Q1
    if kien.ma_mh not in con_lai:               # C2 = K
        return NGOAI_DON                        # Q2
    if kien.so_luong > con_lai[kien.ma_mh]:     # C3 = K
        return VUOT_SO_LUONG                    # Q3
    return CHAP_NHAN                            # Q4
