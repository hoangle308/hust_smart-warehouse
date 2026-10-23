"""Sinh file 02_seed.sql -- du lieu mau nhat quan voi 6 kich ban KB1..KB6.

Chay:  python db/seed/tao_du_lieu_mau.py   (ghi de db/seed/02_seed.sql)

Phan bo the RFID (ma EPC = epc(n), n la so thu tu):
  1..10  : 10 kien TRONG_KHO o khu A (CAP-00001 x5, CAP-00002 x5)  -> KB5, KB6
  11..14 : 4 kien TRONG_KHO o khu B (RES-00002)
  21..23 : 3 kien KHAI_BAO cho don DDH-0001                      -> KB1
  24     : kien KHAI_BAO mat hang ngoai don (ICS-00001)          -> KB3 (Q2)
  25     : kien KHAI_BAO vuot so luong (CAP-00003 x200)          -> KB3 (Q3)
  26..60 : the CHUA_DUNG cho khai bao thu cong (TC1)
  999    : the khong ton tai trong he thong                      -> KB2 (Q1)
Ham epc() va cac danh sach nay duoc dung lai trong device/kich_ban.py.
"""
import hashlib
import os
from datetime import date, timedelta

SALT_CO_DINH = "kho-btl-ktpm"  # muoi co dinh chi cho du lieu mau


def epc(n: int) -> str:
    """Ma EPC 96 bit (24 ky tu hexa), tien to co dinh + so thu tu."""
    return f"E2801160{n:016X}"


def bam_mat_khau(mat_khau: str, muoi: str = SALT_CO_DINH, vong: int = 100_000) -> str:
    h = hashlib.pbkdf2_hmac("sha256", mat_khau.encode(), muoi.encode(), vong).hex()
    return f"pbkdf2_sha256${vong}${muoi}${h}"


def q(v) -> str:
    """Trich dan gia tri cho T-SQL."""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "N'" + str(v).replace("'", "''") + "'"


def ins(bang: str, cot: list[str], hang: list[tuple]) -> str:
    gia_tri = ",\n  ".join("(" + ", ".join(q(x) for x in r) + ")" for r in hang)
    return f"INSERT INTO kho.{bang} ({', '.join(cot)}) VALUES\n  {gia_tri};\n"


def tao() -> str:
    out = ["-- Du lieu mau: sinh tu db/seed/tao_du_lieu_mau.py, khong sua tay\n"]

    # ---- Khu: A uu tien tu dien (CAP), B uu tien dien tro (RES), C du phong;
    #      N cua nhap, X cua xuat, W khu cho
    out.append(ins("KHU", ["MaKhu", "TenKhu", "NhomHangUuTien", "LaKhuDuPhong"], [
        ("A", "Khu A - Tụ điện", "CAP", 0), ("B", "Khu B - Điện trở", "RES", 0),
        ("C", "Khu C - Dự phòng", None, 1), ("N", "Cửa nhập", None, 0),
        ("X", "Cửa xuất", None, 0), ("W", "Khu chờ", None, 0)]))

    vi_tri = []
    for khu in "ABC":
        for day in (1, 2):
            for ke in (1, 2):
                for o in range(1, 6):
                    vi_tri.append((f"{khu}-{day:02d}-{ke:02d}-{o:02d}", khu, day, ke, o, 1))
    for khu in "NXW":
        vi_tri.append((f"{khu}-01-01-01", khu, 1, 1, 1, 99))
    out.append(ins("VI_TRI", ["MaViTri", "MaKhu", "Day", "Ke", "O", "SucChua"], vi_tri))

    mat_hang = [
        ("CAP-00001", "Tụ gốm 100nF 50V", "CAP", "cuộn"), ("CAP-00002", "Tụ gốm 10uF 25V", "CAP", "cuộn"),
        ("CAP-00003", "Tụ hóa 470uF 35V", "CAP", "hộp"), ("CAP-00004", "Tụ tantalum 22uF", "CAP", "cuộn"),
        ("CAP-00005", "Tụ film 1uF 275VAC", "CAP", "hộp"), ("CAP-00006", "Tụ gốm 1nF 50V", "CAP", "cuộn"),
        ("CAP-00007", "Tụ hóa 100uF 16V", "CAP", "hộp"),
        ("RES-00001", "Điện trở 10k 1% 0603", "RES", "cuộn"), ("RES-00002", "Điện trở 1k 1% 0603", "RES", "cuộn"),
        ("RES-00003", "Điện trở 100R 1% 0805", "RES", "cuộn"), ("RES-00004", "Điện trở 4k7 1% 0603", "RES", "cuộn"),
        ("RES-00005", "Điện trở công suất 1R 2W", "RES", "hộp"), ("RES-00006", "Biến trở 10k", "RES", "hộp"),
        ("RES-00007", "Điện trở shunt 10mR", "RES", "cuộn"),
        ("ICS-00001", "Vi điều khiển ESP32-WROOM-32E", "ICS", "khay"), ("ICS-00002", "IC nguồn AMS1117-3.3", "ICS", "cuộn"),
        ("ICS-00003", "IC giao tiếp MAX485", "ICS", "cuộn"), ("ICS-00004", "Op-amp LM358", "ICS", "cuộn"),
        ("ICS-00005", "EEPROM 24C02", "ICS", "cuộn"), ("ICS-00006", "Driver động cơ TB6612FNG", "ICS", "khay"),
    ]
    out.append(ins("MAT_HANG", ["MaMH", "TenMH", "NhomHang", "DonViTinh"], mat_hang))

    out.append(ins("NHA_CUNG_CAP", ["MaNCC", "TenNCC", "DiaChi", "DienThoai"], [
        ("NCC-0001", "Công ty Linh kiện Phương Nam", "Hà Nội", "0241234567"),
        ("NCC-0002", "Công ty Bán dẫn Đông Á", "TP. Hồ Chí Minh", "0287654321")]))
    out.append(ins("KHACH_HANG", ["MaKH", "TenKH", "DiaChi", "DienThoai"], [
        ("KH-0001", "Công ty Điện tử Sao Mai", "Bắc Ninh", "0222111222"),
        ("KH-0002", "Xưởng lắp ráp Hòa Lạc", "Hà Nội", "0243334444")]))

    out.append(ins("NHAN_VIEN", ["MaNV", "HoTen", "VaiTro", "TenDangNhap", "MatKhauBam"], [
        ("NV-0001", "Quản trị hệ thống", "QUAN_TRI", "quantri", bam_mat_khau("quantri123")),
        ("NV-0002", "Nguyễn Văn Kho", "THU_KHO", "thukho", bam_mat_khau("thukho123")),
        ("NV-0003", "Trần Văn Bốc", "NV_KHO", "nvkho", bam_mat_khau("nvkho123")),
        ("NV-0004", "Lê Thị Quản", "QUAN_LY", "quanly", bam_mat_khau("quanly123"))]))

    out.append(ins("THIET_BI", ["MaTB", "LoaiTB", "MoTaViTriLap"], [
        ("GT-01", "CONG_NHAP", "Cổng RFID tại cửa nhập"), ("GT-02", "CONG_XUAT", "Cổng RFID tại cửa xuất"),
        ("HH-01", "CAM_TAY", "Đầu đọc cầm tay"), ("AGV-01", "AGV", "Xe tự hành số 1"),
        ("AGV-02", "AGV", "Xe tự hành số 2")]))

    dang_dung = list(range(1, 15)) + list(range(21, 26))
    the = [(epc(n), "DANG_DUNG" if n in dang_dung else "CHUA_DUNG") for n in list(range(1, 15)) + list(range(21, 61))]
    out.append(ins("THE_RFID", ["MaEPC", "TrangThai"], the))

    kien = []
    goc = date(2026, 9, 1)
    for i in range(1, 11):  # khu A, ngay nhap tang dan -> FIFO xac dinh
        mh = "CAP-00001" if i <= 5 else "CAP-00002"
        o = i if i <= 5 else i - 5
        ke = 1 if i <= 5 else 2
        kien.append((f"KI-2609-{i:05d}", epc(i), mh, 100, f"A-01-{ke:02d}-{o:02d}", "TRONG_KHO",
                     str(goc + timedelta(days=i)) + " 08:00:00"))
    for j, n in enumerate(range(11, 15), start=1):
        kien.append((f"KI-2609-{n:05d}", epc(n), "RES-00002", 500, f"B-01-01-{j:02d}", "TRONG_KHO",
                     str(goc + timedelta(days=n)) + " 08:00:00"))
    kien += [  # kien da khai bao (TC1), cho qua cong nhap
        ("KI-2610-00021", epc(21), "CAP-00003", 100, None, "KHAI_BAO", None),
        ("KI-2610-00022", epc(22), "CAP-00003", 100, None, "KHAI_BAO", None),
        ("KI-2610-00023", epc(23), "RES-00001", 200, None, "KHAI_BAO", None),
        ("KI-2610-00024", epc(24), "ICS-00001", 50, None, "KHAI_BAO", None),
        ("KI-2610-00025", epc(25), "CAP-00003", 200, None, "KHAI_BAO", None),
    ]
    out.append(ins("KIEN_HANG", ["MaKien", "MaEPC", "MaMH", "SoLuong", "MaViTri", "TrangThai", "NgayNhap"], kien))

    out.append(ins("DON_DAT_HANG", ["SoDDH", "NgayDat", "MaNCC"], [
        ("DDH-0001", "2026-10-01", "NCC-0001"), ("DDH-0002", "2026-10-02", "NCC-0002")]))
    out.append(ins("DONG_DDH", ["SoDDH", "MaMH", "SoLuongDat"], [
        ("DDH-0001", "CAP-00003", 300), ("DDH-0001", "RES-00001", 200), ("DDH-0002", "ICS-00002", 100)]))
    return "".join(out)


if __name__ == "__main__":
    dich = os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_seed.sql")
    with open(dich, "w", encoding="utf-8") as f:
        f.write(tao())
    print("Da ghi", dich)
