"""Lop goi REST API cua tang Server. Web app KHONG ket noi CSDL truc tiep (Muc 5.1)."""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")


class LoiAPI(Exception):
    def __init__(self, ma: int, chi_tiet: str):
        super().__init__(chi_tiet)
        self.ma = ma


def _chi_tiet(r: requests.Response) -> str:
    try:
        d = r.json().get("detail", r.text)
    except ValueError:
        return r.text
    if isinstance(d, list):   # loi kiem tra dau vao 422 cua FastAPI
        return "; ".join(f"{'.'.join(str(x) for x in e.get('loc', [])[1:])}: {e.get('msg')}" for e in d)
    return str(d)


def goi(phuong_thuc: str, duong_dan: str, **kw):
    headers = {}
    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = requests.request(phuong_thuc, API_URL + duong_dan, headers=headers, timeout=15, **kw)
    except requests.ConnectionError:
        raise LoiAPI(503, "Không kết nối được tầng Server")
    if r.status_code == 401 and st.session_state.get("token"):
        st.session_state.clear()
        raise LoiAPI(401, "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại")
    if r.status_code >= 400:
        raise LoiAPI(r.status_code, _chi_tiet(r))
    return r.json() if r.content else None


def get(duong_dan: str, **params):
    return goi("GET", duong_dan, params=params or None)


def post(duong_dan: str, du_lieu: dict | None = None):
    return goi("POST", duong_dan, json=du_lieu or {})
