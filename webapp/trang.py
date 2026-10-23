"""Cac man hinh cua Web app (Muc 6.2.2). Moi ham la mot muc don chon."""
import io
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import api_client as api
from api_client import LoiAPI

NHAN = {  # nhan tieng Viet cho cac gia tri ma
    "CHAP_NHAN": "Chấp nhận (Q4)", "THE_CHUA_DANG_KY": "Thẻ chưa đăng ký (Q1)",
    "NGOAI_DON": "Ngoài đơn (Q2)", "VUOT_SO_LUONG": "Vượt số lượng (Q3)", "NGOAI_PHIEU": "Ngoài phiếu xuất",
    "KHAI_BAO": "Khai báo", "TRONG_KHO": "Trong kho", "DA_XUAT": "Đã xuất", "THAT_LAC": "Thất lạc",
    "CHO_GIAO": "Chờ giao", "DA_GIAO": "Đã giao", "DANG_THUC_HIEN": "Đang thực hiện",
    "HOAN_THANH": "Hoàn thành", "LOI": "Lỗi", "TRUC_TUYEN": "🟢 Trực tuyến", "NGOAI_TUYEN": "🔴 Ngoại tuyến",
    "DANG_NHAN": "Đang nhận", "DA_LAP": "Đã lập", "DA_XAC_NHAN": "Đã xác nhận", "HUY": "Hủy",
    "MO": "Đang quét", "CHO_DUYET": "Chờ duyệt", "DONG": "Đã đóng",
    "KHOP": "Khớp", "THIEU": "Thiếu", "THUA": "Thừa", "SAI_VI_TRI": "Sai vị trí",
    "CAT": "Cất", "LAY": "Lấy", "CHO": "Chờ xử lý", "XONG": "Xong",
}


def bang(du_lieu, cot: dict[str, str] | None = None, **kw):
    """Hien thi danh sach dict thanh bang; doi ma sang nhan tieng Viet."""
    if not du_lieu:
        st.caption("Không có dữ liệu.")
        return
    df = pd.DataFrame(du_lieu)
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(lambda v: NHAN.get(v, v) if isinstance(v, str) else v)
    if cot:
        df = df[[c for c in cot if c in df.columns]].rename(columns=cot)
    st.dataframe(df, hide_index=True, use_container_width=True, **kw)


def xu_ly_loi(ham):
    """Bao loi nghiep vu tu Server bang thong bao, khong lam vo trang."""
    try:
        return ham()
    except LoiAPI as e:
        st.error(f"{e} (mã {e.ma})")
        return None


def tai_excel(du_lieu, ten_file: str):
    if du_lieu:
        bo_dem = io.BytesIO()
        pd.DataFrame(du_lieu).to_excel(bo_dem, index=False)
        st.download_button("Tải Excel", bo_dem.getvalue(), ten_file,
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ====================== Bang dieu khien
def bang_dieu_khien():
    st.header("Bảng điều khiển")

    @st.fragment(run_every="5s")
    def noi_dung():
        d = xu_ly_loi(lambda: api.get("/bang-dieu-khien"))
        if not d:
            return
        c = st.columns(4)
        c[0].metric("Kiện trong kho", d["SoKienTrongKho"])
        c[1].metric("Nhiệm vụ đang chạy", d["NhiemVuDangChay"], f"{d['NhiemVuLoi']} lỗi", delta_color="inverse")
        c[2].metric("Thiết bị trực tuyến", f"{d['ThietBiTrucTuyen']}/{d['TongThietBi']}")
        c[3].metric("Sai lệch 24 giờ", d["SaiLech24h"])
        c = st.columns(4)
        c[0].metric("Kiện chờ nhập", d["SoKienChoNhap"])
        c[1].metric("Phiếu nhập đang nhận", d["PhieuNhapDangNhan"])
        c[2].metric("Phiếu xuất chờ xác nhận", d["PhieuXuatChoXacNhan"])
        c[3].metric("Phiên kiểm kê chờ duyệt", d["PhienChoDuyet"])
        trai, phai = st.columns(2)
        with trai:
            st.subheader("Thiết bị")
            bang(xu_ly_loi(lambda: api.get("/thiet-bi/trang-thai")),
                 {"MaTB": "Thiết bị", "LoaiTB": "Loại", "TrangThai": "Trạng thái", "BanTinCuoi": "Bản tin cuối"})
        with phai:
            st.subheader("Sai lệch gần đây")
            bang(d["saiLechGanDay"], {"SoChungTu": "Chứng từ", "MaEPC": "Mã EPC", "KetQua": "Kết quả",
                                      "ThoiDiem": "Thời điểm"})
        st.subheader("Nhiệm vụ vận chuyển chưa xong")
        nv = [x for x in (xu_ly_loi(lambda: api.get("/nhiem-vu")) or [])
              if x["TrangThai"] not in ("HOAN_THANH",)][:15]
        bang(nv, {"MaNVu": "Nhiệm vụ", "LoaiNVu": "Loại", "MaKien": "Kiện", "ViTriDi": "Từ",
                  "ViTriDen": "Đến", "MaTB": "AGV", "TrangThai": "Trạng thái"})

    noi_dung()


# ====================== Nhap kho (2.1, 2.3, 2.5)
def nhap_kho():
    st.header("Nhập kho")
    tab_nhan, tab_kien, tab_ds = st.tabs(["Nhận hàng tại cổng", "Khai báo kiện", "Phiếu nhập"])
    with tab_nhan:
        dang_nhan = xu_ly_loi(lambda: api.get("/phieu-giao/dang-nhan"))
        if not dang_nhan:
            st.info("Chưa có lô hàng nào đang nhận. Chọn đơn đặt hàng để tiếp nhận phiếu giao (2.1).")
            don = xu_ly_loi(lambda: api.get("/don-dat-hang")) or []
            if don:
                chon = st.selectbox("Đơn đặt hàng", [d["SoDDH"] for d in don],
                                    format_func=lambda s: next(f"{s} – {d['TenNCC']}" for d in don if d["SoDDH"] == s))
                bang(next(d["dong"] for d in don if d["SoDDH"] == chon),
                     {"MaMH": "Mặt hàng", "SoLuongDat": "Số lượng đặt"})
                if st.button("Tiếp nhận phiếu giao", type="primary"):
                    kq = xu_ly_loi(lambda: api.post("/phieu-giao", {"soDDH": chon}))
                    if kq:
                        st.success(f"Đã mở phiếu {kq['soPN']}. Cho hàng đi qua cổng nhập GT-01.")
                        st.rerun()
        else:
            _doi_chieu_dang_nhan(dang_nhan)
    with tab_kien:
        khai_bao_kien(tieu_de=False)
    with tab_ds:
        bang(xu_ly_loi(lambda: api.get("/phieu-nhap")),
             {"SoPN": "Số phiếu", "NgayNhap": "Ngày", "SoDDH": "Đơn đặt hàng", "SoKien": "Số kiện",
              "TrangThai": "Trạng thái", "MaNV": "Người lập"})


def _doi_chieu_dang_nhan(pn: dict):
    so_pn = pn["SoPN"]
    st.subheader(f"Phiếu {so_pn} – đơn {pn['SoDDH']}")

    @st.fragment(run_every="3s")
    def ket_qua():
        kq = xu_ly_loi(lambda: api.get(f"/phieu-giao/{so_pn}/doi-chieu"))
        if not kq:
            return
        st.markdown("**Kiện được chấp nhận** (Q4)")
        bang(kq["chapNhan"], {"MaKien": "Kiện", "MaMH": "Mặt hàng", "TenMH": "Tên", "SoLuong": "SL",
                              "MaViTri": "Vị trí hiện tại", "TrangThai": "Trạng thái"})
        st.markdown("**Thông báo sai lệch** (gửi Phòng Mua hàng)")
        if kq["saiLech"]:
            bang(kq["saiLech"], {"MaEPC": "Mã EPC", "KetQua": "Kết quả đối chiếu", "ThoiDiem": "Thời điểm"})
        else:
            st.caption("Không có sai lệch.")
        st.markdown("**Số lượng còn phải nhận theo đơn**")
        bang(kq["conLai"], {"MaMH": "Mặt hàng", "ConLai": "Còn phải nhận"})

    ket_qua()
    if st.session_state.get("vai_tro") == "THU_KHO" and st.button("Lập phiếu nhập (2.5)", type="primary"):
        kq = xu_ly_loi(lambda: api.post(f"/phieu-nhap/{so_pn}/lap"))
        if kq:
            st.session_state.bien_ban = kq
            st.rerun()
    if bb := st.session_state.get("bien_ban"):
        _bien_ban(bb)


def _bien_ban(bb: dict):
    dau = bb["bienBan"]
    with st.container(border=True):
        st.markdown(f"### BIÊN BẢN GIAO NHẬN\nSố phiếu nhập: **{dau['SoPN']}** · Đơn đặt hàng: {dau['SoDDH']} · "
                    f"Nhà cung cấp: {dau['TenNCC']} · Ngày: {str(dau['NgayNhap'])[:16]}")
        bang(bb["dong"], {"MaMH": "Mặt hàng", "TenMH": "Tên", "SoKien": "Số kiện", "SoLuongNhan": "Số lượng nhận"})
        st.caption("Đại diện nhà cung cấp ký ............   Thủ kho ký ............   (thủ tục TC2)")
        if st.button("Đóng biên bản"):
            del st.session_state["bien_ban"]
            st.rerun()


# ====================== Khai bao kien (2.2, thu tuc TC1)
def khai_bao_kien(tieu_de: bool = True):
    if tieu_de:
        st.header("Khai báo kiện")
    st.caption("TC1: dán thẻ lên mặt bên kiện, tránh bề mặt kim loại; chọn mặt hàng, nhập số lượng, quét thẻ.")
    mh = xu_ly_loi(lambda: api.get("/mat-hang")) or []
    the = xu_ly_loi(lambda: api.get("/the-rfid", trangThai="CHUA_DUNG")) or []
    with st.form("khai_bao", clear_on_submit=True):
        ma_mh = st.selectbox("Mặt hàng", [m["MaMH"] for m in mh],
                             format_func=lambda x: next(f"{x} – {m['TenMH']}" for m in mh if m["MaMH"] == x))
        so_luong = st.number_input("Số lượng trong kiện", min_value=1, value=100, step=1)
        ma_epc = st.selectbox("Thẻ RFID (quét bằng đầu đọc cầm tay)", [t["MaEPC"] for t in the])
        if st.form_submit_button("Khai báo", type="primary") and ma_epc:
            kq = xu_ly_loi(lambda: api.post("/kien", {"maMH": ma_mh, "soLuong": int(so_luong), "maEPC": ma_epc}))
            if kq:
                st.success(f"Đã tạo kiện {kq['maKien']}")
    bang(xu_ly_loi(lambda: api.get("/kien", trangThai="KHAI_BAO")),
         {"MaKien": "Kiện chờ nhập", "MaEPC": "Mã EPC", "MaMH": "Mặt hàng", "SoLuong": "SL"})


# ====================== Xuat kho (3.1 - 3.4)
def xuat_kho():
    st.header("Xuất kho")
    tab_yc, tab_px = st.tabs(["Yêu cầu xuất", "Phiếu xuất"])
    with tab_yc:
        dt = xu_ly_loi(lambda: api.get("/doi-tac")) or {"khachHang": []}
        mh = xu_ly_loi(lambda: api.get("/mat-hang")) or []
        with st.form("yeu_cau"):
            ma_kh = st.selectbox("Khách hàng", [k["MaKH"] for k in dt["khachHang"]],
                                 format_func=lambda x: next(f"{x} – {k['TenKH']}" for k in dt["khachHang"] if k["MaKH"] == x))
            dong = st.data_editor(pd.DataFrame([{"maMH": "CAP-00001", "soLuong": 150}]), num_rows="dynamic",
                                  column_config={"maMH": st.column_config.SelectboxColumn("Mặt hàng", options=[m["MaMH"] for m in mh], required=True),
                                                 "soLuong": st.column_config.NumberColumn("Số lượng", min_value=1, required=True)},
                                  use_container_width=True)
            if st.form_submit_button("Tạo yêu cầu xuất (3.1)", type="primary"):
                ds = [{"maMH": r.maMH, "soLuong": int(r.soLuong)} for r in dong.dropna().itertuples()]
                kq = xu_ly_loi(lambda: api.post("/yeu-cau-xuat", {"maKH": ma_kh, "dong": ds}))
                if kq:
                    st.success(f"Đã tạo {kq['soYC']}")
        for yc in xu_ly_loi(lambda: api.get("/yeu-cau-xuat")) or []:
            with st.container(border=True):
                trai, phai = st.columns([4, 1])
                trai.markdown(f"**{yc['SoYC']}** · {yc['TenKH']} · " +
                              ", ".join(f"{d['MaMH']} × {d['SoLuongYC']}" for d in yc["dong"]))
                if yc["SoPX"]:
                    phai.caption(f"Phiếu {yc['SoPX']}")
                elif phai.button("Lập phiếu xuất", key=yc["SoYC"]):
                    kq = xu_ly_loi(lambda: api.post(f"/yeu-cau-xuat/{yc['SoYC']}/lap-phieu"))
                    if kq:
                        st.success(f"Đã lập {kq['soPX']} (FIFO): " + ", ".join(k["maKien"] for k in kq["kien"]))
    with tab_px:
        @st.fragment(run_every="3s")
        def ds_phieu():
            for px in xu_ly_loi(lambda: api.get("/phieu-xuat")) or []:
                with st.expander(f"{px['SoPX']} · {px['MaKH']} · {NHAN.get(px['TrangThai'])}",
                                 expanded=px["TrangThai"] == "DA_LAP"):
                    bang(px["dong"], {"MaKien": "Kiện", "MaEPC": "Mã EPC", "MaMH": "Mặt hàng", "SoLuong": "SL",
                                      "MaViTri": "Vị trí", "TrangThai": "Trạng thái"})
        ds_phieu()


# ====================== Nhiem vu (4.2, 4.3, TC4)
def nhiem_vu():
    st.header("Nhiệm vụ vận chuyển")
    loc = st.segmented_control("Trạng thái", ["Chưa xong", "Lỗi", "Tất cả"], default="Chưa xong")
    ds = xu_ly_loi(lambda: api.get("/nhiem-vu")) or []
    if loc == "Chưa xong":
        ds = [x for x in ds if x["TrangThai"] != "HOAN_THANH"]
    elif loc == "Lỗi":
        ds = [x for x in ds if x["TrangThai"] == "LOI"]
    bang(ds, {"MaNVu": "Nhiệm vụ", "LoaiNVu": "Loại", "MaKien": "Kiện", "MaMH": "Mặt hàng", "ViTriDi": "Từ",
              "ViTriDen": "Đến", "MaTB": "AGV", "TrangThai": "Trạng thái", "TgTao": "Tạo lúc"})
    if st.session_state.get("vai_tro") == "THU_KHO":
        treo = [x["MaNVu"] for x in ds if x["TrangThai"] != "HOAN_THANH"]
        if treo:
            st.subheader("Xác nhận hoàn thành thủ công (TC4)")
            st.caption("Dùng khi AGV lỗi và nhân viên đã cất/lấy hàng bằng xe nâng tay, đã quét thẻ tại vị trí đích.")
            ma = st.selectbox("Nhiệm vụ", treo)
            if st.button("Xác nhận hoàn thành"):
                if xu_ly_loi(lambda: api.post(f"/nhiem-vu/{ma}/xac-nhan-thu-cong")):
                    st.success(f"{ma} đã hoàn thành")
                    st.rerun()


# ====================== Kiem ke (5.1 - 5.3)
def kiem_ke():
    st.header("Kiểm kê")
    phien = xu_ly_loi(lambda: api.get("/kiem-ke")) or []
    dang_mo = next((p for p in phien if p["TrangThai"] == "MO"), None)
    if not dang_mo:
        khu = [k["MaKhu"] for k in (xu_ly_loi(lambda: api.get("/khu")) or []) if k["MaKhu"] not in "NXW"]
        c1, c2 = st.columns([3, 1])
        ma_khu = c1.selectbox("Khu kiểm kê", khu)
        if c2.button("Lập phiên (5.1)", type="primary"):
            if kq := xu_ly_loi(lambda: api.post("/kiem-ke", {"maKhu": ma_khu})):
                st.success(f"Đã lập {kq['maPhien']}. Quét khu bằng đầu đọc cầm tay HH-01 (TC5).")
                st.rerun()
    else:
        st.subheader(f"Phiên {dang_mo['MaPhien']} – khu {dang_mo['MaKhu']} đang quét")

        @st.fragment(run_every="3s")
        def da_quet():
            kq = xu_ly_loi(lambda: api.get(f"/kiem-ke/{dang_mo['MaPhien']}/ket-qua"))
            if kq:
                st.metric("Kiện đã quét", len(kq["dong"]))
                bang(kq["dong"], {"MaKien": "Kiện", "MaEPC": "Mã EPC", "MaMH": "Mặt hàng", "MaViTri": "Vị trí sổ sách"})
        da_quet()
        if st.button("Hoàn tất quét, đối chiếu tồn (5.3)", type="primary"):
            if kq := xu_ly_loi(lambda: api.post(f"/kiem-ke/{dang_mo['MaPhien']}/doi-chieu")):
                st.success("Kết quả: " + ", ".join(f"{NHAN.get(k, k)} {v}" for k, v in kq["tongHop"].items()))
                st.rerun()
    st.subheader("Các phiên")
    bang(phien, {"MaPhien": "Phiên", "MaKhu": "Khu", "NgayKK": "Ngày", "SoDong": "Số dòng", "TrangThai": "Trạng thái"})
    xem = [p["MaPhien"] for p in phien if p["TrangThai"] != "MO"]
    if xem:
        ma = st.selectbox("Xem kết quả phiên", xem)
        kq = xu_ly_loi(lambda: api.get(f"/kiem-ke/{ma}/ket-qua"))
        if kq:
            bang(kq["dong"], {"MaKien": "Kiện", "MaMH": "Mặt hàng", "MaViTri": "Vị trí", "KetQua": "Kết quả",
                              "TrangThai": "Trạng thái kiện"})


# ====================== Phe duyet chenh lech (5.4, TC6)
def phe_duyet():
    st.header("Phê duyệt chênh lệch kiểm kê")
    cho = [p for p in (xu_ly_loi(lambda: api.get("/kiem-ke")) or []) if p["TrangThai"] == "CHO_DUYET"]
    if not cho:
        st.info("Không có phiên nào chờ duyệt.")
        return
    ma = st.selectbox("Phiên", [p["MaPhien"] for p in cho])
    kq = xu_ly_loi(lambda: api.get(f"/kiem-ke/{ma}/ket-qua"))
    if not kq:
        return
    chenh = [d for d in kq["dong"] if d["KetQua"] != "KHOP"]
    st.caption(f"{len(kq['dong']) - len(chenh)} kiện khớp, {len(chenh)} dòng chênh lệch.")
    if chenh:
        df = pd.DataFrame([{"maKien": d["MaKien"], "Mặt hàng": d["MaMH"], "Vị trí sổ sách": d["MaViTri"],
                            "Kết quả": NHAN[d["KetQua"]], "dieuChinh": False} for d in chenh])
        df = st.data_editor(df, hide_index=True, disabled=["maKien", "Mặt hàng", "Vị trí sổ sách", "Kết quả"],
                            column_config={"dieuChinh": st.column_config.CheckboxColumn("Điều chỉnh sổ"),
                                           "maKien": "Kiện"}, use_container_width=True)
        st.caption("Không chọn = Điều tra thêm. Kiện Thiếu được điều chỉnh sẽ chuyển sang Thất lạc.")
    else:
        df = pd.DataFrame(columns=["maKien", "dieuChinh"])
    if st.button("Phê duyệt và đóng phiên", type="primary"):
        qd = [{"maKien": r.maKien, "dieuChinh": bool(r.dieuChinh)} for r in df.itertuples()]
        if kq := xu_ly_loi(lambda: api.post(f"/kiem-ke/{ma}/xu-ly", {"quyetDinh": qd})):
            st.success(f"Đã đóng {ma}; điều chỉnh {len(kq['daDieuChinh'])} kiện")
            st.rerun()


# ====================== Tra cuu (6.2)
def tra_cuu():
    st.header("Tra cứu vị trí, tồn kho")
    q = st.text_input("Mã hoặc tên mặt hàng, mã kiện, mã EPC", placeholder="ví dụ: CAP-00001, tụ gốm")
    if q:
        kq = xu_ly_loi(lambda: api.get("/tra-cuu/vi-tri", q=q)) or []
        st.caption(f"{len(kq)} kiện, tổng {sum(k['SoLuong'] for k in kq)} đơn vị")
        bang(kq, {"MaKien": "Kiện", "MaMH": "Mặt hàng", "TenMH": "Tên", "SoLuong": "SL", "MaViTri": "Vị trí",
                  "NgayNhap": "Ngày nhập"})


# ====================== Bao cao (6.1, 6.3)
def bao_cao():
    st.header("Báo cáo")
    t1, t2, t3, t4 = st.tabs(["Tồn kho", "Nhập – xuất – tồn", "Hiệu suất kho", "Bảng kê chứng từ"])
    with t1:
        d = xu_ly_loi(lambda: api.get("/bao-cao/ton-kho"))
        bang(d, {"MaMH": "Mặt hàng", "TenMH": "Tên", "DonViTinh": "ĐVT", "SoLuongTon": "Tồn", "SoKien": "Số kiện"})
        tai_excel(d, "ton-kho.xlsx")
    with t2:
        tu = st.date_input("Từ ngày (kỳ báo cáo tính đến hiện tại)", date.today() - timedelta(days=30))
        d = xu_ly_loi(lambda: api.get("/bao-cao/nhap-xuat-ton", tuNgay=str(tu)))
        bang(d, {"MaMH": "Mặt hàng", "TenMH": "Tên", "DonViTinh": "ĐVT", "TonDau": "Tồn đầu", "Nhap": "Nhập",
                 "Xuat": "Xuất", "TonCuoi": "Tồn cuối"})
        tai_excel(d, f"nhap-xuat-ton-{tu}.xlsx")
    with t3:
        d = xu_ly_loi(lambda: api.get("/bao-cao/hieu-suat"))
        if d:
            st.subheader("Điều phối AGV")
            bang(d["agv"], {"MaTB": "AGV", "SoNhiemVu": "Nhiệm vụ", "HoanThanh": "Hoàn thành",
                            "ThoiGianTBGiay": "Thời gian TB (giây)"})
            st.subheader("Mức sử dụng ô kệ")
            k = pd.DataFrame(d["khu"])
            if not k.empty:
                k["TyLe"] = (100 * k["SoODaDung"] / k["SoO"]).round(1)
                st.bar_chart(k, x="MaKhu", y="TyLe", y_label="% ô đã dùng", x_label="Khu")
    with t4:
        tu = st.date_input("Từ ngày", date.today().replace(day=1), key="bk")
        d = xu_ly_loi(lambda: api.get("/bao-cao/bang-ke-chung-tu", tuNgay=str(tu)))
        bang(d, {"SoChungTu": "Số chứng từ", "Loai": "Loại", "Ngay": "Ngày"})
        tai_excel(d, f"bang-ke-chung-tu-{tu}.xlsx")


# ====================== Danh muc (1.1 - 1.4)
def danh_muc():
    st.header("Danh mục")
    vai_tro = st.session_state.get("vai_tro")
    t1, t2, t3, t4, t5 = st.tabs(["Mặt hàng", "Đối tác", "Khu và vị trí", "Thẻ RFID", "Thiết bị"])
    with t1:
        bang(xu_ly_loi(lambda: api.get("/mat-hang")),
             {"MaMH": "Mã", "TenMH": "Tên", "NhomHang": "Nhóm", "DonViTinh": "ĐVT"})
        if vai_tro == "THU_KHO":
            with st.form("mat_hang", clear_on_submit=True):
                c = st.columns(4)
                ma, ten = c[0].text_input("Mã (vd CAP-00008)"), c[1].text_input("Tên")
                nhom, dvt = c[2].text_input("Nhóm (3 chữ)"), c[3].text_input("Đơn vị tính")
                if st.form_submit_button("Thêm mặt hàng"):
                    if xu_ly_loi(lambda: api.post("/mat-hang", {"maMH": ma, "tenMH": ten, "nhomHang": nhom,
                                                                "donViTinh": dvt})):
                        st.success("Đã thêm")
    with t2:
        d = xu_ly_loi(lambda: api.get("/doi-tac")) or {}
        st.subheader("Nhà cung cấp")
        bang(d.get("nhaCungCap"))
        st.subheader("Khách hàng")
        bang(d.get("khachHang"))
    with t3:
        khu = xu_ly_loi(lambda: api.get("/khu")) or []
        bang(khu, {"MaKhu": "Khu", "TenKhu": "Tên", "NhomHangUuTien": "Nhóm ưu tiên", "LaKhuDuPhong": "Dự phòng"})
        ma_khu = st.selectbox("Sơ đồ khu", [k["MaKhu"] for k in khu if k["MaKhu"] not in "NXW"])
        vt = pd.DataFrame(xu_ly_loi(lambda: api.get("/vi-tri", maKhu=ma_khu)) or [])
        if not vt.empty:
            vt["Kệ"] = vt["MaViTri"].str[2:7]
            vt["Ô"] = vt["MaViTri"].str[8:]
            vt["Nội dung"] = vt.apply(lambda r: (r["MaMH"] or "") if r["MaKien"] else
                                      ("đặt trước" if r["TrangThai"] == "DAT_TRUOC" else "·"), axis=1)
            st.dataframe(vt.pivot_table(index="Kệ", columns="Ô", values="Nội dung", aggfunc="first"),
                         use_container_width=True)
            st.caption("Hàng: Dãy-Kệ; cột: Ô. “·” là ô trống.")
    with t4:
        bang(xu_ly_loi(lambda: api.get("/the-rfid")), {"MaEPC": "Mã EPC", "TrangThai": "Trạng thái",
                                                       "NgayDangKy": "Ngày đăng ký"}, height=300)
        if vai_tro == "QUAN_TRI":
            with st.form("the", clear_on_submit=True):
                ma = st.text_input("Mã EPC mới (24 ký tự hexa)")
                if st.form_submit_button("Đăng ký thẻ"):
                    if xu_ly_loi(lambda: api.post("/the-rfid", {"maEPC": ma.strip().upper()})):
                        st.success("Đã đăng ký")
    with t5:
        bang(xu_ly_loi(lambda: api.get("/thiet-bi")), {"MaTB": "Thiết bị", "LoaiTB": "Loại",
                                                       "MoTaViTriLap": "Vị trí lắp", "TrangThai": "Trạng thái"})


# ====================== Quan tri
def nguoi_dung():
    st.header("Người dùng")
    bang(xu_ly_loi(lambda: api.get("/nguoi-dung")),
         {"MaNV": "Mã", "HoTen": "Họ tên", "VaiTro": "Vai trò", "TenDangNhap": "Đăng nhập", "TrangThai": "Trạng thái"})
    with st.form("nguoi_dung", clear_on_submit=True):
        c = st.columns(3)
        ma, ten, vai_tro = c[0].text_input("Mã (NV-0005)"), c[1].text_input("Họ tên"), \
            c[2].selectbox("Vai trò", ["NV_KHO", "THU_KHO", "QUAN_LY", "QUAN_TRI"])
        c = st.columns(2)
        dn, mk = c[0].text_input("Tên đăng nhập"), c[1].text_input("Mật khẩu", type="password")
        if st.form_submit_button("Thêm người dùng"):
            if xu_ly_loi(lambda: api.post("/nguoi-dung", {"maNV": ma, "hoTen": ten, "vaiTro": vai_tro,
                                                          "tenDangNhap": dn, "matKhau": mk})):
                st.success("Đã thêm")


def giam_sat():
    st.header("Giám sát thiết bị")

    @st.fragment(run_every="3s")
    def noi_dung():
        bang(xu_ly_loi(lambda: api.get("/thiet-bi/trang-thai")),
             {"MaTB": "Thiết bị", "LoaiTB": "Loại", "TrangThai": "Trạng thái", "BanTinCuoi": "Bản tin cuối"})
        st.subheader("Bản tin gần đây")
        st.caption("Bản tin gửi lại trùng mã không được ghi lần hai (khóa MaBanTin, Mục 6.3).")
        bang(xu_ly_loi(lambda: api.get("/ban-tin", soLuong=50)),
             {"ThoiDiemNhan": "Nhận lúc", "MaTB": "Thiết bị", "ChuDe": "Chủ đề", "TrangThaiXuLy": "Xử lý",
              "MaBanTin": "Mã bản tin"})
    noi_dung()
