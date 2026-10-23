"""HT4 - Module "Tiep nhan ban tin" (nhanh luong vao cua LCT Hinh 6.3).

Lay ban tin hop le (doc MQTT -> kiem tra hop dong -> kiem tra trung), roi phan
phoi sang bo xu ly nghiep vu theo loai thiet bi. Kho luu ban tin duoc truyen
vao (KhoBanTin) nen module khong phu thuoc CSDL -- mau thu MT-07, MT-08.
"""
import json
import logging
from typing import Callable, Protocol

from pydantic import ValidationError

from ht4_thiet_bi.hop_dong import BanTinDocThe, BanTinNhiemVu, TrangThaiThietBi, phan_tich_chu_de

log = logging.getLogger(__name__)

XONG, TRUNG, TU_CHOI, LOI = "XONG", "TRUNG", "TU_CHOI", "LOI"


class KhoBanTin(Protocol):
    def ghi_moi(self, ma_ban_tin: str, ma_tb: str, chu_de: str, noi_dung: str) -> bool:
        """Ghi ban tin trang thai CHO; tra False neu ma ban tin da ton tai."""
    def danh_dau(self, ma_ban_tin: str, trang_thai: str) -> None: ...
    def loai_thiet_bi(self, ma_tb: str) -> str | None: ...
    def cap_nhat_trang_thai_tb(self, ma_tb: str, trang_thai: str) -> None: ...
    def ban_tin_cho(self) -> list[tuple[str, str]]:
        """Cac ban tin con CHO: (chu_de, noi_dung) -- dung khi phuc hoi."""


class BoTiepNhan:
    def __init__(self, kho: KhoBanTin, xu_ly: dict[str, Callable]):
        """xu_ly: loai thiet bi (CONG_NHAP, CONG_XUAT, CAM_TAY, AGV) -> ham nghiep vu."""
        self.kho = kho
        self.xu_ly = xu_ly

    def _kiem_tra(self, chu_de: str, du_lieu: bytes):
        kenh, ma_tb = phan_tich_chu_de(chu_de)
        obj = json.loads(du_lieu)
        model = {"doc-the": BanTinDocThe, "nhiem-vu": BanTinNhiemVu,
                 "trang-thai": TrangThaiThietBi}[kenh]
        bt = model.model_validate(obj)
        if bt.maTB != ma_tb:
            raise ValueError(f"maTB {bt.maTB} không khớp chủ đề {chu_de}")
        return kenh, ma_tb, bt

    def tiep_nhan(self, chu_de: str, du_lieu: bytes) -> str:
        try:
            kenh, ma_tb, bt = self._kiem_tra(chu_de, du_lieu)
        except (ValueError, ValidationError) as e:   # JSONDecodeError cung la ValueError
            log.warning("Từ chối bản tin %s: %s", chu_de, e)
            return TU_CHOI

        loai = self.kho.loai_thiet_bi(ma_tb)
        kenh_sai_loai = (kenh == "nhiem-vu" and loai != "AGV") or (kenh == "doc-the" and loai == "AGV")
        if loai is None or kenh_sai_loai:
            log.warning("Từ chối bản tin %s: thiết bị %s (%s) không hợp lệ cho kênh", chu_de, ma_tb, loai)
            return TU_CHOI

        if kenh == "trang-thai":
            self.kho.cap_nhat_trang_thai_tb(ma_tb, bt.trangThai)
            return XONG

        ma = str(bt.maBanTin)
        if not self.kho.ghi_moi(ma, ma_tb, chu_de, du_lieu.decode("utf-8")):
            log.info("Bỏ qua bản tin trùng %s", ma)
            return TRUNG
        return self._xu_ly(loai, bt)

    def _xu_ly(self, loai: str, bt) -> str:
        ma = str(bt.maBanTin)
        try:
            self.xu_ly[loai](bt)
        except Exception:
            log.exception("Lỗi xử lý bản tin %s", ma)
            self.kho.danh_dau(ma, LOI)
            return LOI
        self.kho.danh_dau(ma, XONG)
        return XONG

    def phuc_hoi(self) -> int:
        """Xu ly tiep cac ban tin con CHO sau su co (nguyen tac bien moc, Muc 6.3)."""
        n = 0
        for chu_de, noi_dung in self.kho.ban_tin_cho():
            try:
                _, ma_tb, bt = self._kiem_tra(chu_de, noi_dung.encode("utf-8"))
            except (ValueError, ValidationError):
                continue
            loai = self.kho.loai_thiet_bi(ma_tb)
            if loai in self.xu_ly:
                self._xu_ly(loai, bt)
                n += 1
        return n
