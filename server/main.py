"""Tang Server - diem khoi chay (FastAPI). Chay: uvicorn main:app --host 0.0.0.0 --port 8000

Khi khoi dong: (1) khoi tao CSDL neu chua co; (2) phuc hoi ban tin con CHO;
(3) ket noi MQTT; (4) bat vong dieu phoi AGV. Tai lieu API: /docs (OpenAPI).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pyodbc

import cau_hinh as cfg
from db import khoi_tao_csdl
from ht1_danh_muc.api import router as r_ht1
from ht2_nhap_kho.api import router as r_ht2
from ht2_nhap_kho.dieu_khien import xu_ly_luot_doc_cong
from ht3_xuat_kho.api import router as r_ht3
from ht3_xuat_kho.dieu_khien import xac_nhan_luot_doc_xuat
from ht4_thiet_bi.api import router as r_ht4
from ht4_thiet_bi.dieu_phoi import VongDieuPhoi, cap_nhat_nhiem_vu
from ht4_thiet_bi.kenh_mqtt import KenhMQTT
from ht4_thiet_bi.kho_ban_tin import KhoBanTinSQL
from ht4_thiet_bi.tiep_nhan import BoTiepNhan
from ht5_kiem_ke.api import router as r_ht5
from ht5_kiem_ke.dieu_khien import ghi_nhan_doc_the
from ht6_bao_cao.api import router as r_ht6

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("server")

# Phan phoi ban tin theo loai thiet bi (trung tam bien doi cua HT4, Hinh 6.3)
XU_LY_THEO_THIET_BI = {
    "CONG_NHAP": xu_ly_luot_doc_cong,     # HT2: 2.3 -> 2.4
    "CONG_XUAT": xac_nhan_luot_doc_xuat,  # HT3: 3.4
    "CAM_TAY": ghi_nhan_doc_the,          # HT5: 5.2
    "AGV": cap_nhat_nhiem_vu,             # HT4: 4.2, 4.3
}


@asynccontextmanager
async def vong_doi(app: FastAPI):
    if cfg.KHOI_TAO_CSDL:
        khoi_tao_csdl()
    bo = BoTiepNhan(KhoBanTinSQL(), XU_LY_THEO_THIET_BI)
    log.info("Phục hồi %d bản tin còn chờ", bo.phuc_hoi())
    kenh = KenhMQTT(bo)
    kenh.bat_dau()
    vong = VongDieuPhoi(kenh.phat)
    vong.start()
    yield
    vong.dung()
    kenh.dung()


app = FastAPI(title="Smart Warehouse API", version="1.0.0", lifespan=vong_doi,
              description="Tầng Server của hệ thống quản lý kho thông minh (bài tập lớn KTPM ứng dụng).")


@app.exception_handler(ValueError)
async def loi_nghiep_vu(_: Request, e: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(e)})


@app.exception_handler(LookupError)
async def khong_tim_thay(_: Request, e: LookupError):
    return JSONResponse(status_code=404, content={"detail": str(e).strip("'")})


@app.exception_handler(pyodbc.IntegrityError)
async def vi_pham_rang_buoc(_: Request, e: pyodbc.IntegrityError):
    # Trung khoa, vi pham khoa ngoai hoac CHECK: loi du lieu dau vao, khong phai loi he thong
    return JSONResponse(status_code=409, content={"detail": "Dữ liệu vi phạm ràng buộc toàn vẹn: " + str(e.args[-1])[:300]})


for r in (r_ht1, r_ht2, r_ht3, r_ht4, r_ht5, r_ht6):
    app.include_router(r, prefix="/api/v1")


@app.get("/api/v1/suc-khoe", tags=["Hệ thống"])
def suc_khoe():
    return {"trangThai": "ok"}
