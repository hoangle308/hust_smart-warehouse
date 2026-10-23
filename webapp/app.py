"""Tang Web app (Streamlit, cong 8501). Don chon hai muc theo vai tro (Bang 6.4)."""
import streamlit as st

import api_client as api
import trang

st.set_page_config(page_title="Quản lý kho thông minh", page_icon="📦", layout="wide")

DON_CHON = {
    "NV_KHO": {"Bảng điều khiển": trang.bang_dieu_khien, "Khai báo kiện": trang.khai_bao_kien,
               "Nhiệm vụ": trang.nhiem_vu, "Tra cứu vị trí": trang.tra_cuu},
    "THU_KHO": {"Bảng điều khiển": trang.bang_dieu_khien, "Nhập kho": trang.nhap_kho, "Xuất kho": trang.xuat_kho,
                "Kiểm kê": trang.kiem_ke, "Nhiệm vụ": trang.nhiem_vu, "Danh mục": trang.danh_muc,
                "Tra cứu": trang.tra_cuu, "Báo cáo": trang.bao_cao},
    "QUAN_LY": {"Bảng điều khiển": trang.bang_dieu_khien, "Phê duyệt chênh lệch": trang.phe_duyet,
                "Báo cáo": trang.bao_cao, "Tra cứu": trang.tra_cuu},
    "QUAN_TRI": {"Danh mục": trang.danh_muc, "Người dùng": trang.nguoi_dung, "Giám sát thiết bị": trang.giam_sat},
}
TEN_VAI_TRO = {"NV_KHO": "Nhân viên kho", "THU_KHO": "Thủ kho", "QUAN_LY": "Quản lý", "QUAN_TRI": "Quản trị"}


def dang_nhap():
    _, giua, _ = st.columns([1, 1.2, 1])
    with giua:
        st.title("📦 Quản lý kho thông minh")
        st.caption("Đăng nhập theo vai trò. Tài khoản mẫu: thukho / thukho123, nvkho / nvkho123, "
                   "quanly / quanly123, quantri / quantri123.")
        with st.form("dang_nhap"):
            ten = st.text_input("Tên đăng nhập")
            mk = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng nhập", type="primary", use_container_width=True):
                try:
                    kq = api.post("/auth/dang-nhap", {"tenDangNhap": ten, "matKhau": mk})
                except api.LoiAPI as e:
                    st.error(str(e))
                else:
                    st.session_state.update(token=kq["token"], vai_tro=kq["vaiTro"], ho_ten=kq["hoTen"])
                    st.rerun()


if not st.session_state.get("token"):
    dang_nhap()
else:
    vai_tro = st.session_state.vai_tro
    with st.sidebar:
        st.markdown(f"**{st.session_state.ho_ten}**  \n{TEN_VAI_TRO.get(vai_tro, vai_tro)}")
        muc = st.radio("Đơn chọn", list(DON_CHON[vai_tro]), label_visibility="collapsed")
        st.divider()
        if st.button("Đăng xuất", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    DON_CHON[vai_tro][muc]()
