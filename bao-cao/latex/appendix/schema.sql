-- ============================================================
-- Smart Warehouse -- Script tao co so du lieu (SQL Server)
-- 23 bang: 20 quan he logic + BAN_TIN_THIET_BI + NHAT_KY_KIEM_TOAN + SAI_LECH
-- ============================================================
CREATE SCHEMA kho;
GO
CREATE SCHEMA bao_cao;
GO

-- ---------- Du lieu tham chieu ----------
CREATE TABLE kho.KHU (
  MaKhu           CHAR(1)       NOT NULL PRIMARY KEY,
  TenKhu          NVARCHAR(50)  NOT NULL,
  NhomHangUuTien  CHAR(3)       NULL,
  LaKhuDuPhong    BIT           NOT NULL DEFAULT 0
);
CREATE TABLE kho.VI_TRI (
  MaViTri   VARCHAR(10)  NOT NULL PRIMARY KEY,          -- A-03-02-05
  MaKhu     CHAR(1)      NOT NULL REFERENCES kho.KHU(MaKhu),
  Day       TINYINT      NOT NULL,
  Ke        TINYINT      NOT NULL,
  O         TINYINT      NOT NULL,
  SucChua   TINYINT      NOT NULL DEFAULT 1,
  TrangThai VARCHAR(10)  NOT NULL DEFAULT 'SAN_SANG'
            CHECK (TrangThai IN ('SAN_SANG','DAT_TRUOC','KHOA'))
);

-- ---------- Du lieu chu ----------
CREATE TABLE kho.MAT_HANG (
  MaMH      VARCHAR(9)    NOT NULL PRIMARY KEY,         -- CAP-00125
  TenMH     NVARCHAR(100) NOT NULL,
  NhomHang  CHAR(3)       NOT NULL,
  DonViTinh NVARCHAR(20)  NOT NULL,
  MoTa      NVARCHAR(200) NULL
);
CREATE TABLE kho.NHA_CUNG_CAP (
  MaNCC     VARCHAR(8)    NOT NULL PRIMARY KEY,         -- NCC-0012
  TenNCC    NVARCHAR(100) NOT NULL,
  DiaChi    NVARCHAR(200) NULL,
  DienThoai VARCHAR(15)   NULL
);
CREATE TABLE kho.KHACH_HANG (
  MaKH      VARCHAR(8)    NOT NULL PRIMARY KEY,
  TenKH     NVARCHAR(100) NOT NULL,
  DiaChi    NVARCHAR(200) NULL,
  DienThoai VARCHAR(15)   NULL
);
CREATE TABLE kho.NHAN_VIEN (
  MaNV        VARCHAR(7)    NOT NULL PRIMARY KEY,
  HoTen       NVARCHAR(100) NOT NULL,
  VaiTro      VARCHAR(10)   NOT NULL
              CHECK (VaiTro IN ('QUAN_TRI','THU_KHO','NV_KHO','QUAN_LY')),
  TenDangNhap VARCHAR(50)   NOT NULL UNIQUE,
  MatKhauBam  VARCHAR(200)  NOT NULL,
  TrangThai   VARCHAR(10)   NOT NULL DEFAULT 'HOAT_DONG'
              CHECK (TrangThai IN ('HOAT_DONG','KHOA'))
);
CREATE TABLE kho.THE_RFID (
  MaEPC      CHAR(24)    NOT NULL PRIMARY KEY,
  TrangThai  VARCHAR(10) NOT NULL DEFAULT 'CHUA_DUNG'
             CHECK (TrangThai IN ('CHUA_DUNG','DANG_DUNG','HONG')),
  NgayDangKy DATE        NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE)
);
CREATE TABLE kho.KIEN_HANG (
  MaKien    VARCHAR(13)  NOT NULL PRIMARY KEY,          -- KI-2610-00342
  MaEPC     CHAR(24)     NOT NULL REFERENCES kho.THE_RFID(MaEPC),
  MaMH      VARCHAR(9)   NOT NULL REFERENCES kho.MAT_HANG(MaMH),
  SoLuong   INT          NOT NULL CHECK (SoLuong > 0),
  MaViTri   VARCHAR(10)  NULL REFERENCES kho.VI_TRI(MaViTri),
  TrangThai VARCHAR(10)  NOT NULL DEFAULT 'KHAI_BAO'
            CHECK (TrangThai IN ('KHAI_BAO','TRONG_KHO','DA_XUAT','THAT_LAC')),
  NgayNhap  DATETIME2(0) NULL
);
CREATE TABLE kho.THIET_BI (
  MaTB         VARCHAR(6)    NOT NULL PRIMARY KEY,      -- GT-01, AGV-01
  LoaiTB       VARCHAR(10)   NOT NULL
               CHECK (LoaiTB IN ('CONG_NHAP','CONG_XUAT','CAM_TAY','AGV')),
  MoTaViTriLap NVARCHAR(100) NULL,
  TrangThai    VARCHAR(10)   NOT NULL DEFAULT 'NGOAI_TUYEN'
               CHECK (TrangThai IN ('TRUC_TUYEN','NGOAI_TUYEN','LOI'))
);

-- ---------- Du lieu giao dich ----------
CREATE TABLE kho.DON_DAT_HANG (
  SoDDH   VARCHAR(20) NOT NULL PRIMARY KEY,
  NgayDat DATE        NOT NULL,
  MaNCC   VARCHAR(8)  NOT NULL REFERENCES kho.NHA_CUNG_CAP(MaNCC)
);
CREATE TABLE kho.DONG_DDH (
  SoDDH      VARCHAR(20) NOT NULL REFERENCES kho.DON_DAT_HANG(SoDDH),
  MaMH       VARCHAR(9)  NOT NULL REFERENCES kho.MAT_HANG(MaMH),
  SoLuongDat INT         NOT NULL CHECK (SoLuongDat > 0),
  PRIMARY KEY (SoDDH, MaMH)
);
CREATE TABLE kho.PHIEU_NHAP (
  SoPN     VARCHAR(13)  NOT NULL PRIMARY KEY,           -- PN-261006-001
  NgayNhap DATETIME2(0) NOT NULL,
  SoDDH    VARCHAR(20)  NOT NULL REFERENCES kho.DON_DAT_HANG(SoDDH),
  MaNV     VARCHAR(7)   NOT NULL REFERENCES kho.NHAN_VIEN(MaNV),
  TrangThai VARCHAR(10) NOT NULL DEFAULT 'DANG_NHAN'
            CHECK (TrangThai IN ('DANG_NHAN','DA_LAP'))
);
CREATE TABLE kho.DONG_PHIEU_NHAP (
  SoPN   VARCHAR(13) NOT NULL REFERENCES kho.PHIEU_NHAP(SoPN),
  MaKien VARCHAR(13) NOT NULL REFERENCES kho.KIEN_HANG(MaKien),
  PRIMARY KEY (SoPN, MaKien)
);
CREATE TABLE kho.YEU_CAU_XUAT (
  SoYC   VARCHAR(13) NOT NULL PRIMARY KEY,
  NgayYC DATE        NOT NULL,
  MaKH   VARCHAR(8)  NOT NULL REFERENCES kho.KHACH_HANG(MaKH)
);
CREATE TABLE kho.DONG_YC_XUAT (
  SoYC      VARCHAR(13) NOT NULL REFERENCES kho.YEU_CAU_XUAT(SoYC),
  MaMH      VARCHAR(9)  NOT NULL REFERENCES kho.MAT_HANG(MaMH),
  SoLuongYC INT         NOT NULL CHECK (SoLuongYC > 0),
  PRIMARY KEY (SoYC, MaMH)
);
CREATE TABLE kho.PHIEU_XUAT (
  SoPX      VARCHAR(13)  NOT NULL PRIMARY KEY,
  NgayXuat  DATETIME2(0) NOT NULL,
  SoYC      VARCHAR(13)  NOT NULL REFERENCES kho.YEU_CAU_XUAT(SoYC),
  MaNV      VARCHAR(7)   NOT NULL REFERENCES kho.NHAN_VIEN(MaNV),
  TrangThai VARCHAR(10)  NOT NULL DEFAULT 'DA_LAP'
            CHECK (TrangThai IN ('DA_LAP','DA_XAC_NHAN','HUY'))
);
CREATE TABLE kho.DONG_PHIEU_XUAT (
  SoPX    VARCHAR(13) NOT NULL REFERENCES kho.PHIEU_XUAT(SoPX),
  MaKien  VARCHAR(13) NOT NULL REFERENCES kho.KIEN_HANG(MaKien),
  MaMH    VARCHAR(9)  NOT NULL,   -- lap tu KIEN_HANG: chung tu giu gia tri luc lap
  SoLuong INT         NOT NULL,
  PRIMARY KEY (SoPX, MaKien)
);
CREATE TABLE kho.NHIEM_VU_VC (
  MaNVu       VARCHAR(13)  NOT NULL PRIMARY KEY,
  LoaiNVu     VARCHAR(10)  NOT NULL CHECK (LoaiNVu IN ('CAT','LAY','CHUYEN')),
  MaKien      VARCHAR(13)  NOT NULL REFERENCES kho.KIEN_HANG(MaKien),
  ViTriDi     VARCHAR(10)  NOT NULL REFERENCES kho.VI_TRI(MaViTri),
  ViTriDen    VARCHAR(10)  NOT NULL REFERENCES kho.VI_TRI(MaViTri),
  MaTB        VARCHAR(6)   NULL REFERENCES kho.THIET_BI(MaTB),
  TrangThai   VARCHAR(15)  NOT NULL DEFAULT 'CHO_GIAO'
              CHECK (TrangThai IN ('CHO_GIAO','DA_GIAO','DANG_THUC_HIEN','HOAN_THANH','LOI')),
  TgTao       DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
  TgHoanThanh DATETIME2(0) NULL
);
CREATE TABLE kho.PHIEN_KIEM_KE (
  MaPhien   VARCHAR(13) NOT NULL PRIMARY KEY,
  MaKhu     CHAR(1)     NOT NULL REFERENCES kho.KHU(MaKhu),
  MaNV      VARCHAR(7)  NOT NULL REFERENCES kho.NHAN_VIEN(MaNV),
  NgayKK    DATE        NOT NULL,
  TrangThai VARCHAR(10) NOT NULL DEFAULT 'MO'
            CHECK (TrangThai IN ('MO','CHO_DUYET','DONG'))
);
CREATE TABLE kho.DONG_KIEM_KE (
  MaPhien VARCHAR(13) NOT NULL REFERENCES kho.PHIEN_KIEM_KE(MaPhien),
  MaKien  VARCHAR(13) NOT NULL REFERENCES kho.KIEN_HANG(MaKien),
  KetQua  VARCHAR(12) NOT NULL
          CHECK (KetQua IN ('KHOP','THIEU','THUA','SAI_VI_TRI')),
  PRIMARY KEY (MaPhien, MaKien)
);

-- ---------- Bang bo sung o thiet ke (kiem soat, phuc hoi) ----------
CREATE TABLE kho.SAI_LECH (
  MaSL        BIGINT IDENTITY(1,1) PRIMARY KEY,
  LoaiChungTu CHAR(2)          NOT NULL CHECK (LoaiChungTu IN ('PN','PX')),
  SoChungTu   VARCHAR(13)      NOT NULL,
  MaEPC       CHAR(24)         NOT NULL,
  KetQua      VARCHAR(20)      NOT NULL
              CHECK (KetQua IN ('THE_CHUA_DANG_KY','NGOAI_DON','VUOT_SO_LUONG','NGOAI_PHIEU')),
  ThoiDiem    DATETIME2(0)     NOT NULL DEFAULT SYSDATETIME(),
  MaBanTin    UNIQUEIDENTIFIER NULL
);
CREATE TABLE kho.BAN_TIN_THIET_BI (
  MaBanTin      UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,  -- chong ghi trung
  MaTB          VARCHAR(6)       NOT NULL REFERENCES kho.THIET_BI(MaTB),
  ChuDe         VARCHAR(100)     NOT NULL,
  NoiDung       NVARCHAR(MAX)    NOT NULL,
  ThoiDiemNhan  DATETIME2(3)     NOT NULL DEFAULT SYSDATETIME(),
  TrangThaiXuLy VARCHAR(10)      NOT NULL DEFAULT 'CHO'
                CHECK (TrangThaiXuLy IN ('CHO','XONG','LOI'))
);
CREATE TABLE kho.NHAT_KY_KIEM_TOAN (
  MaNK       BIGINT IDENTITY(1,1) PRIMARY KEY,
  ThoiDiem   DATETIME2(3)  NOT NULL DEFAULT SYSDATETIME(),
  MaNV       VARCHAR(7)    NULL,
  Bang       VARCHAR(50)   NOT NULL,
  KhoaBanGhi VARCHAR(50)   NOT NULL,
  ThaoTac    CHAR(1)       NOT NULL CHECK (ThaoTac IN ('I','U','D')),
  GiaTriCu   NVARCHAR(MAX) NULL,
  GiaTriMoi  NVARCHAR(MAX) NULL
);
GO

-- ---------- Tep chi dan (Muc 6.4.3) ----------
-- Chi dan co loc: the duoc tai su dung sau khi kien da xuat
CREATE UNIQUE INDEX UX_KIEN_EPC  ON kho.KIEN_HANG (MaEPC) WHERE TrangThai IN ('KHAI_BAO','TRONG_KHO');
CREATE INDEX IX_KIEN_MH_TT       ON kho.KIEN_HANG (MaMH, TrangThai, NgayNhap) INCLUDE (MaViTri, SoLuong);
CREATE INDEX IX_KIEN_VITRI       ON kho.KIEN_HANG (MaViTri);
CREATE INDEX IX_VITRI_KHU_TT     ON kho.VI_TRI (MaKhu, TrangThai);
CREATE INDEX IX_NVU_TT_TB        ON kho.NHIEM_VU_VC (TrangThai, MaTB);
GO

-- ---------- Thuoc tinh tinh huong: ton kho (view co chi dan) ----------
CREATE VIEW bao_cao.TON_KHO WITH SCHEMABINDING AS
  SELECT MaMH, SUM(SoLuong) AS SoLuongTon, COUNT_BIG(*) AS SoKien
  FROM kho.KIEN_HANG
  WHERE TrangThai = 'TRONG_KHO'
  GROUP BY MaMH;
GO
CREATE UNIQUE CLUSTERED INDEX UX_TON_KHO ON bao_cao.TON_KHO (MaMH);
GO

-- ---------- Nhat ky kiem toan: vi du cho KIEN_HANG ----------
CREATE TRIGGER kho.TR_KIEN_HANG_KIEM_TOAN ON kho.KIEN_HANG
AFTER UPDATE AS
BEGIN
  SET NOCOUNT ON;
  INSERT INTO kho.NHAT_KY_KIEM_TOAN (MaNV, Bang, KhoaBanGhi, ThaoTac, GiaTriCu, GiaTriMoi)
  SELECT CAST(SESSION_CONTEXT(N'MaNV') AS VARCHAR(7)), 'KIEN_HANG', i.MaKien, 'U',
         CONCAT(d.TrangThai, '|', d.MaViTri), CONCAT(i.TrangThai, '|', i.MaViTri)
  FROM inserted i JOIN deleted d ON d.MaKien = i.MaKien;
END;
GO

-- ---------- Phan quyen (Muc 6.3) ----------
CREATE ROLE r_ung_dung;
GRANT SELECT, INSERT, UPDATE ON SCHEMA::kho TO r_ung_dung;
GRANT DELETE ON kho.MAT_HANG TO r_ung_dung;
DENY  DELETE ON kho.PHIEU_NHAP TO r_ung_dung;
DENY  DELETE ON kho.PHIEU_XUAT TO r_ung_dung;
CREATE ROLE r_bao_cao;
GRANT SELECT ON SCHEMA::bao_cao TO r_bao_cao;
GO
