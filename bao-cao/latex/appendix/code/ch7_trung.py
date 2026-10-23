def ghi_moi(self, ma_ban_tin, ma_tb, chu_de, noi_dung) -> bool:
    try:
        with giao_tac() as cur:
            cur.execute("INSERT INTO kho.BAN_TIN_THIET_BI "
                        "(MaBanTin, MaTB, ChuDe, NoiDung) VALUES (?,?,?,?)",
                        ma_ban_tin, ma_tb, chu_de, noi_dung)
        return True
    except pyodbc.IntegrityError as e:
        if any(m in str(e) for m in _LOI_TRUNG_KHOA):
            return False          # ban tin trung: bo qua
        raise
