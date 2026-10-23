"""MT-07, MT-08: module Tiep nhan ban tin (HT4) voi kho ban tin gia lap."""
import json
import uuid

from ht4_thiet_bi.tiep_nhan import LOI, TRUNG, TU_CHOI, XONG, BoTiepNhan

EPC = "E2801160000000000000000A"


class KhoGia:
    def __init__(self):
        self.ban_tin, self.trang_thai_tb = {}, {}
        self.loai = {"GT-01": "CONG_NHAP", "AGV-01": "AGV"}

    def ghi_moi(self, ma, ma_tb, chu_de, noi_dung):
        if ma in self.ban_tin:
            return False
        self.ban_tin[ma] = ["CHO", chu_de, noi_dung]
        return True

    def danh_dau(self, ma, tt):
        self.ban_tin[ma][0] = tt

    def loai_thiet_bi(self, ma_tb):
        return self.loai.get(ma_tb)

    def cap_nhat_trang_thai_tb(self, ma_tb, tt):
        self.trang_thai_tb[ma_tb] = tt

    def ban_tin_cho(self):
        return [(c, n) for tt, c, n in self.ban_tin.values() if tt == "CHO"]


def doc_the(ma_tb="GT-01", ma=None, **ghi_de):
    bt = {"v": 1, "maBanTin": ma or str(uuid.uuid4()), "maTB": ma_tb,
          "thoiDiem": "2026-10-13T09:15:02+07:00", "the": [{"maEPC": EPC, "cuongDo": -52}]}
    bt.update(ghi_de)
    return json.dumps(bt).encode()


def bo_tiep_nhan():
    goi = []
    return BoTiepNhan(KhoGia(), {"CONG_NHAP": goi.append, "AGV": goi.append}), goi


def test_ban_tin_hop_le_duoc_xu_ly():
    bo, goi = bo_tiep_nhan()
    assert bo.tiep_nhan("kho/thietbi/GT-01/doc-the", doc_the()) == XONG
    assert len(goi) == 1 and goi[0].the[0].maEPC == EPC


def test_mt07_ban_tin_trung_bi_bo_qua():
    bo, goi = bo_tiep_nhan()
    ma = str(uuid.uuid4())
    assert bo.tiep_nhan("kho/thietbi/GT-01/doc-the", doc_the(ma=ma)) == XONG
    assert bo.tiep_nhan("kho/thietbi/GT-01/doc-the", doc_the(ma=ma)) == TRUNG
    assert len(goi) == 1


def test_mt08_sai_hop_dong_thieu_ma_epc():
    bo, goi = bo_tiep_nhan()
    du_lieu = doc_the(the=[{"cuongDo": -52}])
    assert bo.tiep_nhan("kho/thietbi/GT-01/doc-the", du_lieu) == TU_CHOI
    assert goi == [] and bo.kho.ban_tin == {}


def test_tu_choi_json_hong_epc_sai_va_ma_tb_gia_mao():
    bo, _ = bo_tiep_nhan()
    assert bo.tiep_nhan("kho/thietbi/GT-01/doc-the", b"{khong phai json") == TU_CHOI
    assert bo.tiep_nhan("kho/thietbi/GT-01/doc-the", doc_the(the=[{"maEPC": "XYZ"}])) == TU_CHOI
    # thiet bi gui ban tin mang ma thiet bi khac voi chu de cua no
    assert bo.tiep_nhan("kho/thietbi/GT-01/doc-the", doc_the(ma_tb="GT-02")) == TU_CHOI
    assert bo.tiep_nhan("kho/thietbi/GT-09/doc-the", doc_the(ma_tb="GT-09")) == TU_CHOI


def test_agv_khong_duoc_gui_doc_the():
    bo, _ = bo_tiep_nhan()
    assert bo.tiep_nhan("kho/thietbi/AGV-01/doc-the", doc_the(ma_tb="AGV-01")) == TU_CHOI


def test_trang_thai_thiet_bi():
    bo, _ = bo_tiep_nhan()
    du_lieu = json.dumps({"v": 1, "maTB": "AGV-01", "trangThai": "NGOAI_TUYEN"}).encode()
    assert bo.tiep_nhan("kho/thietbi/AGV-01/trang-thai", du_lieu) == XONG
    assert bo.kho.trang_thai_tb["AGV-01"] == "NGOAI_TUYEN"


def test_loi_nghiep_vu_danh_dau_loi_va_phuc_hoi():
    kho = KhoGia()

    def hong(_):
        raise RuntimeError("CSDL tạm mất kết nối")
    bo = BoTiepNhan(kho, {"CONG_NHAP": hong})
    assert bo.tiep_nhan("kho/thietbi/GT-01/doc-the", doc_the()) == LOI
    # ban tin con CHO (vi du server tat giua chung) duoc xu ly lai khi khoi dong
    goi = []
    ma = str(uuid.uuid4())
    kho.ghi_moi(ma, "GT-01", "kho/thietbi/GT-01/doc-the", doc_the(ma=ma).decode())
    assert BoTiepNhan(kho, {"CONG_NHAP": goi.append}).phuc_hoi() == 1
    assert kho.ban_tin[ma][0] == XONG and len(goi) == 1
