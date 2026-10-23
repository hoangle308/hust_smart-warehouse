"""Kiem tra moi man hinh Web app hien thi khong loi theo tung vai tro (Streamlit AppTest).

Tang Server duoc thay bang du lieu API mau; kiem tra web app chi phu thuoc REST API.
"""
import os
import sys

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
WEBAPP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp")

MAU = {
    "/bang-dieu-khien": {"SoKienTrongKho": 14, "SoKienChoNhap": 5, "PhieuNhapDangNhan": 1, "PhieuXuatChoXacNhan": 0,
                         "NhiemVuDangChay": 2, "NhiemVuLoi": 0, "ThietBiTrucTuyen": 5, "TongThietBi": 5,
                         "SaiLech24h": 1, "PhienChoDuyet": 1,
                         "saiLechGanDay": [{"LoaiChungTu": "PN", "SoChungTu": "PN-261013-001",
                                            "MaEPC": "E2801160" + "0" * 13 + "3E7", "KetQua": "THE_CHUA_DANG_KY",
                                            "ThoiDiem": "2026-10-13T10:00:00"}]},
    "/thiet-bi/trang-thai": [{"MaTB": "GT-01", "LoaiTB": "CONG_NHAP", "TrangThai": "TRUC_TUYEN", "BanTinCuoi": None}],
    "/nhiem-vu": [{"MaNVu": "NV-261013-001", "LoaiNVu": "CAT", "MaKien": "KI-2610-00021", "MaMH": "CAP-00003",
                   "ViTriDi": "N-01-01-01", "ViTriDen": "A-02-01-01", "MaTB": "AGV-01",
                   "TrangThai": "DANG_THUC_HIEN", "TgTao": "2026-10-13T10:00:00", "TgHoanThanh": None}],
    "/phieu-giao/dang-nhan": {"SoPN": "PN-261013-001", "SoDDH": "DDH-0001", "NgayNhap": "2026-10-13T10:00:00"},
    "/phieu-giao/PN-261013-001/doi-chieu": {
        "phieu": {}, "chapNhan": [{"MaKien": "KI-2610-00021", "MaEPC": "E", "MaMH": "CAP-00003", "TenMH": "Tụ",
                                   "SoLuong": 100, "MaViTri": "N-01-01-01", "TrangThai": "KHAI_BAO"}],
        "saiLech": [], "conLai": [{"MaMH": "CAP-00003", "ConLai": 200}]},
    "/don-dat-hang": [{"SoDDH": "DDH-0001", "TenNCC": "NCC", "dong": [{"SoDDH": "DDH-0001", "MaMH": "CAP-00003",
                                                                      "SoLuongDat": 300}]}],
    "/phieu-nhap": [], "/mat-hang": [{"MaMH": "CAP-00001", "TenMH": "Tụ gốm", "NhomHang": "CAP", "DonViTinh": "cuộn"}],
    "/the-rfid": [{"MaEPC": "E28011600000000000000001A", "TrangThai": "CHUA_DUNG", "NgayDangKy": "2026-10-01"}],
    "/kien": [], "/doi-tac": {"nhaCungCap": [{"MaNCC": "NCC-0001"}], "khachHang": [{"MaKH": "KH-0001", "TenKH": "Sao Mai"}]},
    "/yeu-cau-xuat": [{"SoYC": "YC-261013-001", "TenKH": "Sao Mai", "SoPX": None,
                       "dong": [{"MaMH": "CAP-00001", "SoLuongYC": 150}]}],
    "/phieu-xuat": [{"SoPX": "PX-261013-001", "MaKH": "KH-0001", "TrangThai": "DA_LAP", "dong": []}],
    "/kiem-ke": [{"MaPhien": "KK-261013-001", "MaKhu": "A", "NgayKK": "2026-10-13", "SoDong": 12,
                  "TrangThai": "CHO_DUYET"}],
    "/kiem-ke/KK-261013-001/ket-qua": {"dong": [
        {"MaKien": "KI-2609-00010", "MaEPC": "E", "MaMH": "CAP-00002", "MaViTri": "A-01-02-05",
         "TrangThai": "TRONG_KHO", "KetQua": "THIEU"},
        {"MaKien": "KI-2609-00001", "MaEPC": "E", "MaMH": "CAP-00001", "MaViTri": "A-01-01-01",
         "TrangThai": "TRONG_KHO", "KetQua": "KHOP"}]},
    "/khu": [{"MaKhu": "A", "TenKhu": "Khu A", "NhomHangUuTien": "CAP", "LaKhuDuPhong": False}],
    "/vi-tri": [{"MaViTri": "A-01-01-01", "MaKhu": "A", "TrangThai": "SAN_SANG", "MaKien": "K", "MaMH": "CAP-00001",
                 "SoLuong": 100}, {"MaViTri": "A-01-01-02", "MaKhu": "A", "TrangThai": "DAT_TRUOC", "MaKien": None,
                                   "MaMH": None, "SoLuong": None}],
    "/thiet-bi": [], "/nguoi-dung": [], "/ban-tin": [],
    "/bao-cao/ton-kho": [{"MaMH": "CAP-00001", "TenMH": "Tụ", "DonViTinh": "cuộn", "SoLuongTon": 500, "SoKien": 5}],
    "/bao-cao/nhap-xuat-ton": [], "/bao-cao/bang-ke-chung-tu": [],
    "/bao-cao/hieu-suat": {"agv": [], "khu": [{"MaKhu": "A", "SoO": 20, "SoODaDung": 12}]},
}

@pytest.fixture(autouse=True)
def api_gia(monkeypatch):
    sys.path.insert(0, WEBAPP)
    import api_client
    monkeypatch.setattr(api_client, "goi", lambda pt, dd, **kw: MAU.get(dd))


def chay(vai_tro: str, muc: str):
    at = st_testing.AppTest.from_file(os.path.join(WEBAPP, "app.py"), default_timeout=30)
    at.session_state["token"], at.session_state["vai_tro"], at.session_state["ho_ten"] = "t", vai_tro, "Kiểm thử"
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    at.sidebar.radio[0].set_value(muc).run()
    return at


@pytest.mark.parametrize("vai_tro,muc", [
    ("THU_KHO", m) for m in ["Bảng điều khiển", "Nhập kho", "Xuất kho", "Kiểm kê", "Nhiệm vụ", "Danh mục",
                             "Tra cứu", "Báo cáo"]] + [
    ("NV_KHO", m) for m in ["Khai báo kiện", "Nhiệm vụ", "Tra cứu vị trí"]] + [
    ("QUAN_LY", m) for m in ["Phê duyệt chênh lệch", "Báo cáo"]] + [
    ("QUAN_TRI", m) for m in ["Danh mục", "Người dùng", "Giám sát thiết bị"]])
def test_man_hinh_hien_thi(vai_tro, muc):
    at = chay(vai_tro, muc)
    assert not at.exception, [e.value for e in at.exception]
    assert at.header[0].value  # moi man hinh co tieu de


def test_don_chon_theo_vai_tro():
    at = chay("NV_KHO", "Bảng điều khiển")
    assert at.sidebar.radio[0].options == ["Bảng điều khiển", "Khai báo kiện", "Nhiệm vụ", "Tra cứu vị trí"]
