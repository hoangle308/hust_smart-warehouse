"""Cau hinh tang Server, doc tu bien moi truong (xem .env.example o goc repo)."""
import os

_THU_MUC = os.path.dirname(os.path.abspath(__file__))

# ---- Co so du lieu
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_NAME = os.getenv("DB_NAME", "SmartWarehouse")
def _chon_driver() -> str:
    """Uu tien driver Microsoft (18, 17); khong co thi dung FreeTDS."""
    try:
        import pyodbc
        co = pyodbc.drivers()
    except Exception:
        co = []
    for ten in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "FreeTDS"):
        if ten in co:
            return ten
    return "ODBC Driver 18 for SQL Server"


ODBC_DRIVER = os.getenv("ODBC_DRIVER") or _chon_driver()
# Tai khoan quan tri: chi dung luc khoi tao CSDL
DB_SA_USER = os.getenv("DB_SA_USER", "sa")
DB_SA_PASSWORD = os.getenv("DB_SA_PASSWORD", "")
# Tai khoan ung dung, quyen toi thieu (role r_ung_dung, r_bao_cao) -- Muc 6.3
DB_APP_USER = os.getenv("DB_APP_USER", "ung_dung")
DB_APP_PASSWORD = os.getenv("DB_APP_PASSWORD", "")
# Chay cuc bo voi SQL Server dung Windows Authentication
DB_TRUSTED = os.getenv("DB_TRUSTED", "0") == "1"
KHOI_TAO_CSDL = os.getenv("KHOI_TAO_CSDL", "1") == "1"
DB_SCRIPT_DIR = os.getenv("DB_SCRIPT_DIR", os.path.join(_THU_MUC, "..", "db"))

# ---- MQTT
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "server")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

# ---- Xac thuc REST
JWT_SECRET = os.getenv("JWT_SECRET", "doi-chuoi-bi-mat-nay")
JWT_HET_HAN_GIO = int(os.getenv("JWT_HET_HAN_GIO", "8"))

# ---- Dieu phoi AGV
CHU_KY_DIEU_PHOI_GIAY = float(os.getenv("CHU_KY_DIEU_PHOI_GIAY", "2"))

# ---- Vi tri dac biet (khu N, X, W -- Bang 4.6)
VI_TRI_CUA_NHAP = "N-01-01-01"
VI_TRI_CUA_XUAT = "X-01-01-01"
VI_TRI_KHU_CHO = "W-01-01-01"
