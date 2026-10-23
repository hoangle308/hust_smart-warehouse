"""Bang dieu khien tang Device (Streamlit, cong 8502): chay KB1..KB6 va doc the tu do."""
import os

import pandas as pd
import streamlit as st

from kich_ban import KICH_BAN, epc
from thiet_bi import AGV, QuanLyThietBi

st.set_page_config(page_title="Tầng Device – Giả lập thiết bị", page_icon="📡", layout="wide")


@st.cache_resource
def quan_ly() -> QuanLyThietBi:
    return QuanLyThietBi(os.getenv("MQTT_HOST", "localhost"), int(os.getenv("MQTT_PORT", "1883")),
                         os.getenv("MQTT_DEVICE_PASSWORD", "")).bat_dau()


ql = quan_ly()
st.title("Tầng Device – giả lập thiết bị kho")
st.caption("Mỗi thiết bị là một MQTT client riêng. Hợp đồng bản tin: docs/contracts. "
           "Thao tác trên Web app (cổng 8501) theo cột *Chuẩn bị* trước khi bấm.")


@st.fragment(run_every="2s")
def trang_thai():
    cot = st.columns(len(ql.thiet_bi))
    for c, (ma, tb) in zip(cot, ql.thiet_bi.items()):
        nhan = "🟢 Trực tuyến" if tb.truc_tuyen else "🔴 Ngoại tuyến"
        phu = f"đệm {len(tb.bo_dem)}"
        if isinstance(tb, AGV):
            phu += f" · {tb.nhiem_vu_hien_tai or 'rảnh'}" + (" · KB4 sẵn sàng" if tb.loi_lan_toi else "")
        c.metric(ma, nhan, phu, delta_color="off")


trang_thai()

st.subheader("Kịch bản kiểm thử")
for kb in KICH_BAN:
    with st.container(border=True):
        trai, phai = st.columns([5, 1])
        trai.markdown(f"**{kb.ma} – {kb.ten}**  \n*Chuẩn bị:* {kb.chuan_bi}  \n*Mong đợi:* {kb.mong_doi}")
        if phai.button(f"Chạy {kb.ma}", key=kb.ma, use_container_width=True):
            if kb.thiet_bi:
                ql.doc(kb.thiet_bi, list(kb.ds_epc))
                st.toast(f"{kb.thiet_bi} đã gửi {len(kb.ds_epc)} thẻ")
            else:
                ql.thiet_bi["AGV-01"].loi_lan_toi = True
                st.toast("AGV-01 sẽ mất kết nối ở nhiệm vụ kế tiếp")

with st.expander("Đọc thẻ tự do"):
    ma_tb = st.selectbox("Thiết bị", ["GT-01", "GT-02", "HH-01"])
    goi_y = "\n".join(epc(n) for n in (26, 27))
    ds = st.text_area("Mã EPC, mỗi dòng một mã (24 ký tự hexa)", goi_y)
    if st.button("Gửi lượt đọc"):
        ql.doc(ma_tb, [x.strip().upper() for x in ds.splitlines() if x.strip()])
    st.caption("Thẻ còn trống trong dữ liệu mẫu: số 26–60, ví dụ " + epc(26))


@st.fragment(run_every="2s")
def nhat_ky():
    st.subheader("Nhật ký thiết bị")
    st.dataframe(pd.DataFrame(ql.nhat_ky.doc()[:100], columns=["Giờ", "Thiết bị", "Sự kiện"]),
                 hide_index=True, use_container_width=True)


nhat_ky()
