"""Kich ban kiem thu xuyen ba tang KB1..KB6 (Bang 6.11).

Ma EPC sinh cung cong thuc voi db/seed/tao_du_lieu_mau.py nen khop du lieu mau.
Moi kich ban mo phong "the gioi vat ly": kien nao di qua cong / duoc quet.
"""
from dataclasses import dataclass


def epc(n: int) -> str:
    return f"E2801160{n:016X}"


@dataclass(frozen=True)
class KichBan:
    ma: str
    ten: str
    thiet_bi: str | None      # None: kich ban thay doi hanh vi thiet bi, khong gui luot doc
    ds_epc: tuple[str, ...]
    chuan_bi: str             # thao tac tren Web app truoc khi bam
    mong_doi: str             # ket qua kiem tra tren Web app


KICH_BAN = [
    KichBan("KB4", "AGV-01 mất kết nối ở nhiệm vụ kế tiếp", None, (),
            "Bấm trước KB1 để AGV-01 nhận nhiệm vụ cất đầu tiên của KB1.",
            "AGV-01 chuyển Ngoại tuyến rồi Trực tuyến lại sau ~12 giây; nhiệm vụ hoàn thành đúng 1 lần; "
            "trang Giám sát thiết bị có 1 bản tin bị bỏ qua vì trùng."),
    KichBan("KB1", "Lô hàng khớp đơn qua cổng nhập", "GT-01", (epc(21), epc(22), epc(23)),
            "Thủ kho: Nhập kho → tiếp nhận phiếu giao cho đơn DDH-0001.",
            "3 kiện Chấp nhận (Q4); 3 nhiệm vụ cất được giao và hoàn thành; lập được phiếu nhập; tồn tăng."),
    KichBan("KB2", "Thẻ chưa khai báo qua cổng nhập", "GT-01", (epc(999),),
            "Giữ nguyên phiếu đang nhận của KB1.",
            "Sai lệch \"Thẻ chưa đăng ký\" (Q1)."),
    KichBan("KB3", "Kiện ngoài đơn và kiện vượt số lượng", "GT-01", (epc(24), epc(25)),
            "Giữ nguyên phiếu đang nhận của KB1 (CAP-00003 còn phải nhận 100).",
            "Sai lệch \"Ngoài đơn\" (Q2) cho ICS-00001 và \"Vượt số lượng\" (Q3) cho kiện CAP-00003 x200."),
    KichBan("KB5", "Kiểm kê khu A, một kiện bị lấy khỏi kệ", "HH-01",
            tuple(epc(n) for n in list(range(1, 10)) + [21, 22]),
            "Lập phiếu nhập của KB1; Thủ kho: Kiểm kê → lập phiên cho khu A.",
            "Sau khi đối chiếu: 1 kiện Thiếu (KI-2609-00010), các kiện còn lại Khớp; phiên chờ duyệt."),
    KichBan("KB6", "Xuất kho theo yêu cầu", "GT-02", (epc(1), epc(2)),
            "Thủ kho: Xuất kho → yêu cầu KH-0001, CAP-00001 x150 → lập phiếu xuất; chờ AGV lấy xong.",
            "Phiếu xuất Đã xác nhận; 2 kiện Đã xuất; thẻ trả về Chưa dùng; tồn CAP-00001 giảm 200 (xuất nguyên kiện)."),
]
