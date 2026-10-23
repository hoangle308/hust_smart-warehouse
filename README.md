# Smart Warehouse — Hệ thống quản lý kho thông minh RFID UHF + AGV

**Bài tập lớn học phần ET3260 – Kỹ thuật phần mềm ứng dụng** · Lớp LT-CTHN-ĐTVT01-K70 · GVHD: ThS. Vũ Song Tùng
Đại học Bách khoa Hà Nội – Trường Điện – Điện tử

| Họ và tên | MSSV |
|---|---|
| Lê Hoàng | 20250407P |
| Lê Trung Hiếu | 20250404P |
| Lê Hùng Công | 20250386P |
| Trần Minh Hiếu | 20250403P |
| Phạm Minh Dũng | 20250389P |

📄 **Báo cáo:** [`bao-cao/BaoCao_SmartWarehouse.pdf`](bao-cao/BaoCao_SmartWarehouse.pdf) · mã nguồn LaTeX: [`bao-cao/latex/`](bao-cao/latex/)

---

Mã nguồn Giai đoạn 5 (Cài đặt) của bài tập lớn môn *Kỹ thuật phần mềm ứng dụng*
(GVHD ThS. Vũ Song Tùng). Hệ thống gồm ba tầng, đúng như thiết kế ở Chương 5–6 của báo cáo:

| Tầng | Thư mục | Công nghệ | Cổng |
|---|---|---|---|
| Device (giả lập thiết bị IoT) | `device/` | Python, paho-mqtt, Streamlit | 8502 |
| Server (máy chủ nghiệp vụ) | `server/` | Python, FastAPI, pyodbc | 8000 |
| Web app (người dùng) | `webapp/` | Python, Streamlit | 8501 |
| CSDL | `db/` | MS SQL Server 2022 | 1433 |
| Môi giới bản tin | `mosquitto/` | Eclipse Mosquitto 2 (MQTT 3.1.1) | 1883 |

Hợp đồng bản tin giữa Device và Server nằm ở `docs/contracts/*.schema.json`. Khi thay
bộ giả lập bằng ESP32 thật, chỉ cần firmware gửi đúng các hợp đồng này; Server không đổi.

```
smart-warehouse/
├── db/schema/01_schema.sql      23 bảng, view tồn kho, trigger kiểm toán, vai trò
├── db/seed/02_seed.sql          dữ liệu mẫu (sinh bởi tao_du_lieu_mau.py)
├── server/ht1_danh_muc …        HT1 Danh mục & phân quyền
│          ht2_nhap_kho …        HT2 Nhập kho (đối chiếu Q1–Q4, phân bổ ô)
│          ht3_xuat_kho …        HT3 Xuất kho (FIFO)
│          ht4_thiet_bi …        HT4 Tiếp nhận bản tin, điều phối AGV
│          ht5_kiem_ke …         HT5 Kiểm kê
│          ht6_bao_cao …         HT6 Báo cáo
├── device/                      5 thiết bị giả lập + 6 kịch bản KB1–KB6
├── webapp/                      giao diện theo vai trò
├── tests/                       kiểm thử đơn vị, tích hợp MQTT, màn hình Web app
├── bao-cao/                     báo cáo PDF và mã nguồn LaTeX
└── docker-compose.yml
```

## 1. Chạy bằng Docker (khuyến nghị)

Yêu cầu: Docker Desktop (≥ 4 GB RAM cho Docker vì SQL Server cần khoảng 2 GB).

```bash
git clone <địa chỉ repo này>
cd smart-warehouse
docker compose up --build     # .env không bắt buộc: compose đã có mật khẩu mặc định
```

Lần đầu mất vài phút (tải ảnh SQL Server, cài ODBC Driver 18). Server tự tạo CSDL
`SmartWarehouse`, nạp lược đồ và dữ liệu mẫu, tạo login ứng dụng `ung_dung`.
Khi thấy dòng `Application startup complete`, mở:

- Web app: <http://localhost:8501>
- Bảng điều khiển thiết bị: <http://localhost:8502>
- Tài liệu API (Swagger): <http://localhost:8000/docs>

Tài khoản mẫu:

| Tên đăng nhập | Mật khẩu | Vai trò |
|---|---|---|
| `quantri` | `quantri123` | Quản trị |
| `thukho` | `thukho123` | Thủ kho |
| `nvkho` | `nvkho123` | Nhân viên kho |
| `quanly` | `quanly123` | Quản lý |

Muốn làm lại từ dữ liệu mẫu ban đầu: `docker compose down -v` rồi `docker compose up`.

**Máy Mac chip Apple (M1–M4):** ảnh SQL Server chỉ có bản amd64. Trong Docker Desktop bật
*Settings → General → Use Rosetta for x86_64/amd64 emulation*; `docker-compose.yml` đã đặt
`platform: linux/amd64` cho dịch vụ `db`.

## 2. Chạy không dùng Docker (SQL Server có sẵn trên máy)

Cần: Python 3.11+, SQL Server (bản Developer/Express) có bật TCP 1433,
[ODBC Driver 18 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server),
và Mosquitto 2.

```bash
conda create -n kho python=3.12 -y && conda activate kho
pip install -r server/requirements.txt -r device/requirements.txt -r webapp/requirements.txt
```

**Mosquitto:** cách nhanh nhất là chỉ chạy riêng dịch vụ này bằng Docker
(`docker compose up mqtt`). Nếu cài Mosquitto trực tiếp, dùng `mosquitto/mosquitto.conf`
và `mosquitto/acl`, tạo tệp mật khẩu cho các tài khoản `server`, `GT-01`, `GT-02`,
`HH-01`, `AGV-01`, `AGV-02` bằng `mosquitto_passwd` (xem `mosquitto/entrypoint.sh`).

Mở ba cửa sổ dòng lệnh (Windows dùng `set TEN=gia_tri` thay cho `export`):

```bash
# 1) Server — dùng Windows Authentication để tạo CSDL lần đầu
cd server
export DB_HOST=localhost DB_TRUSTED=1 DB_APP_PASSWORD='Kho@2026App!'
export MQTT_PASSWORD=mqtt-server-2026 JWT_SECRET=chuoi-bi-mat-dai-it-nhat-32-ky-tu
uvicorn main:app --port 8000

# 2) Web app
cd webapp && export API_URL=http://localhost:8000/api/v1
streamlit run app.py --server.port 8501

# 3) Bảng điều khiển thiết bị
cd device && export MQTT_DEVICE_PASSWORD=mqtt-thiet-bi-2026
streamlit run panel.py --server.port 8502
```

Nếu không dùng Windows Authentication: đặt `DB_TRUSTED=0` và `DB_SA_PASSWORD=<mật khẩu sa>`.

## 3. Kiểm thử xuyên ba tầng (khoảng 10 phút)

Mở Web app (đăng nhập `thukho`) và bảng điều khiển thiết bị cạnh nhau. Làm **đúng thứ tự** dưới
đây vì các kịch bản dùng chung dữ liệu mẫu. Mỗi kịch bản trên bảng điều khiển đều ghi sẵn
phần *Chuẩn bị* và *Mong đợi*.

| Bước | Thao tác | Kết quả mong đợi (xem trên Web app) |
|---|---|---|
| 1 | Bảng thiết bị: bấm **KB4** | AGV-01 được “gài lỗi” cho nhiệm vụ kế tiếp. |
| 2 | Web app: *Nhập kho* → tiếp nhận phiếu giao cho đơn `DDH-0001`. Bảng thiết bị: bấm **KB1** | 3 kiện *Chấp nhận* (Q4); 3 nhiệm vụ cất được giao cho AGV. AGV-01 *Ngoại tuyến* rồi *Trực tuyến* lại sau ~12 giây; nhiệm vụ của nó hoàn thành **đúng một lần**; *Giám sát thiết bị* có 1 bản tin *Trùng* bị bỏ qua. |
| 3 | Bấm **KB2** | Sai lệch “Thẻ chưa đăng ký” (Q1). |
| 4 | Bấm **KB3** | Sai lệch “Ngoài đơn” (Q2) cho ICS-00001 và “Vượt số lượng” (Q3) cho kiện CAP-00003 × 200. |
| 5 | Web app: đợi các nhiệm vụ cất *Hoàn thành* → **Lập phiếu nhập** | Có phiếu `PN-…` và biên bản sai lệch; *Tồn kho* tăng. |
| 6 | Web app: *Kiểm kê* → lập phiên cho khu A. Bấm **KB5** → *Đối chiếu* | 1 kiện *Thiếu* (`KI-2609-00010`), các kiện khác *Khớp*; phiên chờ duyệt. Đăng nhập `quanly` để duyệt. |
| 7 | Web app: *Xuất kho* → yêu cầu `KH-0001`, `CAP-00001` × 150 → **Lập phiếu xuất**; đợi AGV lấy xong. Bấm **KB6** | Phiếu xuất *Đã xác nhận*; 2 kiện *Đã xuất*; thẻ về *Chưa dùng*; tồn CAP-00001 giảm 200 (xuất nguyên kiện). |


## 4. Kiểm thử tự động

```bash
pip install pytest
python -m pytest -q tests
```

- Kiểm thử đơn vị (mẫu thử MT-01 … MT-10): không cần CSDL.
- `test_tich_hop_mqtt.py`: cần lệnh `mosquitto` trong PATH (tự bỏ qua nếu không có);
  kiểm tra ACL, Last Will và chống ghi trùng ở kịch bản KB4.
- `test_webapp.py`: chạy 17 màn hình Web app bằng `streamlit.testing` với API giả.

## 5. Sinh lại hợp đồng bản tin và dữ liệu mẫu

```bash
cd server && python -m ht4_thiet_bi.hop_dong ../docs/contracts
cd db/seed && python tao_du_lieu_mau.py      # ghi đè db/seed/02_seed.sql
```

## 6. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Build `server` lỗi ở bước `apt-get … msodbcsql18` | Mạng chặn `packages.microsoft.com`. Từ bản này Dockerfile tự bỏ qua và dùng driver FreeTDS; log server in dòng `Trình điều khiển ODBC: FreeTDS`. Xem lỗi đầy đủ: `docker compose --progress plain build server`. |
| `db` thoát với `Unable to set system administrator password … too short` | Docker không đọc được `.env` (sai thư mục hoặc tệp bị lưu thành `.env.txt`). Từ bản này `docker-compose.yml` có giá trị mặc định nên chạy được cả khi thiếu `.env`; chạy `docker compose down -v` rồi `docker compose up`. |
| `db` không lên, log báo mật khẩu yếu | Mật khẩu SQL Server cần ≥ 8 ký tự gồm chữ hoa, chữ thường, số, ký tự đặc biệt. Sửa `.env`, chạy `docker compose down -v`. |
| Server báo `Login failed for user 'ung_dung'` | CSDL cũ còn mật khẩu khác: `docker compose down -v` rồi chạy lại. |
| Thiết bị báo *Kết nối bị từ chối* | `MQTT_DEVICE_PASSWORD` ở `.env` không khớp lúc tạo broker; xóa volume `du_lieu_mqtt`. |
| AGV không nhận nhiệm vụ | Xem *Giám sát thiết bị*: AGV phải *Trực tuyến*; vòng điều phối chạy mỗi 2 giây. |
| `Can't open lib 'ODBC Driver 18 for SQL Server'` (chạy không Docker) | Cài ODBC Driver 18, hoặc đặt `ODBC_DRIVER=ODBC Driver 17 for SQL Server`. |
