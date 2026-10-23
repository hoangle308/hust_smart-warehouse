"""MT-10: module Kiem tra quyen (HT1), ca ham thuan lan dependency FastAPI that."""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from ht1_danh_muc.phan_quyen import (NV_KHO, QUAN_LY, THU_KHO, KhongDuQuyen, kiem_tra_quyen,
                                     yeu_cau)
from ht1_danh_muc.xac_thuc import bam_mat_khau, kiem_tra_mat_khau, tao_token

app = FastAPI()


@app.post("/api/v1/kiem-ke/{ma}/xu-ly")
def xu_ly(ma: str, nd=Depends(yeu_cau(QUAN_LY))):
    return {"ok": ma, "nguoiDuyet": nd["maNV"]}


client = TestClient(app)


def test_mt10_ham_kiem_tra_quyen():
    with pytest.raises(KhongDuQuyen):
        kiem_tra_quyen(NV_KHO, (QUAN_LY,))
    kiem_tra_quyen(QUAN_LY, (QUAN_LY, THU_KHO))


def test_mt10_nv_kho_goi_xu_ly_kiem_ke_bi_403():
    token = tao_token("NV-0003", NV_KHO, "Trần Văn Bốc")
    r = client.post("/api/v1/kiem-ke/KK-261013-001/xu-ly", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_quan_ly_duoc_phep_va_chua_dang_nhap_bi_401():
    token = tao_token("NV-0004", QUAN_LY, "Lê Thị Quản")
    r = client.post("/api/v1/kiem-ke/KK-261013-001/xu-ly", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json()["nguoiDuyet"] == "NV-0004"
    assert client.post("/api/v1/kiem-ke/X/xu-ly").status_code == 401
    assert client.post("/api/v1/kiem-ke/X/xu-ly", headers={"Authorization": "Bearer gia-mao"}).status_code == 401


def test_bam_mat_khau_khop_voi_du_lieu_mau():
    import importlib.util, os
    duong_dan = os.path.join(os.path.dirname(__file__), "..", "db", "seed", "tao_du_lieu_mau.py")
    spec = importlib.util.spec_from_file_location("seed", duong_dan)
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    assert kiem_tra_mat_khau("thukho123", seed.bam_mat_khau("thukho123"))
    assert not kiem_tra_mat_khau("sai", seed.bam_mat_khau("thukho123"))
    assert kiem_tra_mat_khau("abc", bam_mat_khau("abc", "muoi"))
