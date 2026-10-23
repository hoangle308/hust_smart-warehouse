"""Hop dong giao tiep MQTT giua Device va Server (Muc 6.2.4, Bang 6.3).

Mot nguon su that duy nhat: tu cac model nay sinh JSON Schema trong
docs/contracts/ (python -m ht4_thiet_bi.hop_dong). ESP32 o do an sau phai
gui dung cac dinh dang nay.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MA_TB = r"^[A-Z]{2,3}-\d{2}$"


class _Goc(BaseModel):
    model_config = ConfigDict(extra="forbid")
    v: Literal[1] = 1


class The(BaseModel):
    model_config = ConfigDict(extra="forbid")
    maEPC: str = Field(pattern=r"^[0-9A-F]{24}$", description="Ma EPC 96 bit, 24 ky tu hexa")
    cuongDo: int | None = Field(default=None, description="RSSI (dBm)")


class BanTinDocThe(_Goc):
    """Topic kho/thietbi/{maTB}/doc-the, QoS 1: mot luot doc cua cong hoac dau doc cam tay."""
    maBanTin: UUID = Field(description="UUID do thiet bi sinh; server bo qua ban tin trung")
    maTB: str = Field(pattern=MA_TB)
    thoiDiem: datetime = Field(description="Thoi diem doc (ISO 8601 co mui gio), khong phai thoi diem gui")
    the: list[The] = Field(min_length=1)


class BanTinNhiemVu(_Goc):
    """Topic kho/agv/{maTB}/nhiem-vu, QoS 1: trang thai thuc hien nhiem vu."""
    maBanTin: UUID
    maTB: str = Field(pattern=MA_TB)
    maNVu: str
    trangThai: Literal["DANG_THUC_HIEN", "HOAN_THANH", "LOI"]
    thoiDiem: datetime


class TrangThaiThietBi(_Goc):
    """Topic kho/thietbi/{maTB}/trang-thai, QoS 1, retain; Last Will gui NGOAI_TUYEN.

    Trang thai la gia tri luy dang (ghi de) nen khong can maBanTin.
    """
    maTB: str = Field(pattern=MA_TB)
    trangThai: Literal["TRUC_TUYEN", "NGOAI_TUYEN", "LOI"]


class LenhNhiemVu(_Goc):
    """Topic kho/agv/{maTB}/lenh, QoS 1: Server -> AGV."""
    maBanTin: UUID
    maNVu: str
    maKien: str
    viTriDi: str
    viTriDen: str
    thoiDiem: datetime


def phan_tich_chu_de(chu_de: str) -> tuple[str, str]:
    """Tra (kenh, maTB) voi kenh in {doc-the, trang-thai, nhiem-vu}; nem ValueError neu sai."""
    p = chu_de.split("/")
    if len(p) == 4 and p[0] == "kho":
        if p[1] == "thietbi" and p[3] in ("doc-the", "trang-thai"):
            return p[3], p[2]
        if p[1] == "agv" and p[3] == "nhiem-vu":
            return p[3], p[2]
    raise ValueError(f"Chủ đề không thuộc hợp đồng: {chu_de}")


if __name__ == "__main__":
    import json
    import os
    import sys
    dich = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "docs", "contracts")
    os.makedirs(dich, exist_ok=True)
    for ten, m in [("doc-the", BanTinDocThe), ("nhiem-vu", BanTinNhiemVu),
                   ("trang-thai", TrangThaiThietBi), ("lenh", LenhNhiemVu)]:
        with open(os.path.join(dich, f"{ten}.schema.json"), "w", encoding="utf-8") as f:
            json.dump(m.model_json_schema(), f, ensure_ascii=False, indent=2)
        print("ghi", ten)
