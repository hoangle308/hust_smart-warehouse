def chon_kien_fifo(ds_kien: list[KienTon], so_luong_can: int) -> list[KienTon]:
    da_chon, tong = [], 0
    for k in sorted(ds_kien, key=lambda k: (k.ngay_nhap, k.ma_kien)):
        if tong >= so_luong_can:
            break
        da_chon.append(k)
        tong += k.so_luong
    if tong < so_luong_can:
        raise KhongDuHang(f"Tồn khả dụng {tong} nhỏ hơn số lượng yêu cầu {so_luong_can}")
    return da_chon
