"""Cai dat KhoBanTin tren SQL Server (bang BAN_TIN_THIET_BI, Bang 6.8)."""
import pyodbc

from db import giao_tac

_LOI_TRUNG_KHOA = ("2627", "2601")


class KhoBanTinSQL:
    def ghi_moi(self, ma_ban_tin, ma_tb, chu_de, noi_dung) -> bool:
        try:
            with giao_tac() as cur:
                cur.execute("INSERT INTO kho.BAN_TIN_THIET_BI (MaBanTin, MaTB, ChuDe, NoiDung) VALUES (?,?,?,?)",
                            ma_ban_tin, ma_tb, chu_de, noi_dung)
            return True
        except pyodbc.IntegrityError as e:
            if any(m in str(e) for m in _LOI_TRUNG_KHOA):
                return False
            raise

    def danh_dau(self, ma_ban_tin, trang_thai) -> None:
        with giao_tac() as cur:
            cur.execute("UPDATE kho.BAN_TIN_THIET_BI SET TrangThaiXuLy = ? WHERE MaBanTin = ?",
                        trang_thai, ma_ban_tin)

    def loai_thiet_bi(self, ma_tb):
        with giao_tac() as cur:
            cur.execute("SELECT LoaiTB FROM kho.THIET_BI WHERE MaTB = ?", ma_tb)
            r = cur.fetchone()
        return r[0] if r else None

    def cap_nhat_trang_thai_tb(self, ma_tb, trang_thai) -> None:
        with giao_tac() as cur:
            cur.execute("UPDATE kho.THIET_BI SET TrangThai = ? WHERE MaTB = ?", trang_thai, ma_tb)

    def ban_tin_cho(self):
        with giao_tac() as cur:
            cur.execute("SELECT ChuDe, NoiDung FROM kho.BAN_TIN_THIET_BI WHERE TrangThaiXuLy = 'CHO' "
                        "ORDER BY ThoiDiemNhan")
            return [(r[0], r[1]) for r in cur.fetchall()]
