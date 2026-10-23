"""Module "Truy cap CSDL" dung chung (module co san tren cac LCT, Hinh 6.1-6.4).

Moi module nghiep vu truy cap du lieu qua giao_tac(); khong module nao giu
ket noi hay bien toan cuc (khong co tuong tac chung -- Muc 6.5).
"""
import logging
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime

import pyodbc

import cau_hinh as cfg

log = logging.getLogger(__name__)


def _chuoi_ket_noi(database: str, user: str, password: str) -> str:
    xac_thuc = "Trusted_Connection=yes;" if cfg.DB_TRUSTED else f"UID={user};PWD={password};"
    if "FreeTDS" in cfg.ODBC_DRIVER:   # driver mo cua kho Debian (khi khong tai duoc driver Microsoft)
        return (f"DRIVER={{{cfg.ODBC_DRIVER}}};SERVER={cfg.DB_HOST};PORT={cfg.DB_PORT};"
                f"DATABASE={database};{xac_thuc}TDS_Version=7.4;ClientCharset=UTF-8;")
    return (f"DRIVER={{{cfg.ODBC_DRIVER}}};SERVER={cfg.DB_HOST},{cfg.DB_PORT};"
            f"DATABASE={database};{xac_thuc}Encrypt=yes;TrustServerCertificate=yes;")


_SET_ANSI = ("SET ANSI_NULLS, ANSI_PADDING, ANSI_WARNINGS, ARITHABORT, CONCAT_NULL_YIELDS_NULL, "
             "QUOTED_IDENTIFIER ON; SET NUMERIC_ROUNDABORT OFF;")


def _mo(chuoi: str, autocommit: bool) -> pyodbc.Connection:
    """Mo ket noi. FreeTDS khong tu bat cac tuy chon ANSI nhu driver Microsoft, ma view
    co chi muc va chi muc co loc (Phu luc B) bat buoc cac tuy chon nay -> bat tuong minh."""
    conn = pyodbc.connect(chuoi, autocommit=autocommit)
    if "FreeTDS" in cfg.ODBC_DRIVER:
        conn.execute(_SET_ANSI)
    return conn


def ket_noi() -> pyodbc.Connection:
    """Ket noi bang tai khoan ung dung (quyen toi thieu)."""
    return _mo(_chuoi_ket_noi(cfg.DB_NAME, cfg.DB_APP_USER, cfg.DB_APP_PASSWORD), autocommit=False)


@contextmanager
def giao_tac(ma_nv: str | None = None):
    """Mot giao tac CSDL. ma_nv duoc ghi vao SESSION_CONTEXT de trigger kiem toan doc."""
    conn = ket_noi()
    cur = conn.cursor()
    try:
        if ma_nv:
            cur.execute("EXEC sp_set_session_context @key=N'MaNV', @value=?", ma_nv)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def thanh_dict(cur) -> list[dict]:
    cot = [c[0] for c in cur.description]
    return [dict(zip(cot, hang)) for hang in cur.fetchall()]


def mot_dong(cur) -> dict | None:
    hang = cur.fetchone()
    if hang is None:
        return None
    return dict(zip([c[0] for c in cur.description], hang))


def truy_van(sql: str, *tham_so) -> list[dict]:
    with giao_tac() as cur:
        cur.execute(sql, *tham_so)
        return thanh_dict(cur)


def sinh_ma(cur, bang: str, cot: str, tien_to: str, so_chu_so: int) -> str:
    """Sinh ma lien tiep theo tien to (Bang 4.6). bang/cot chi lay tu hang so trong ma nguon."""
    cur.execute(f"SELECT MAX({cot}) FROM kho.{bang} WITH (UPDLOCK, HOLDLOCK) WHERE {cot} LIKE ?",
                tien_to + "%")
    cuoi = cur.fetchone()[0]
    so = int(cuoi[len(tien_to):]) + 1 if cuoi else 1
    return f"{tien_to}{so:0{so_chu_so}d}"


def ma_chung_tu(cur, loai: str, bang: str, cot: str) -> str:
    """Ma chung tu: Loai + yymmdd + so thu tu 3 so, vi du PN-261013-001."""
    return sinh_ma(cur, bang, cot, f"{loai}-{datetime.now():%y%m%d}-", 3)


def ma_kien(cur) -> str:
    """Ma kien: KI + yymm + so lien tiep 5 so, vi du KI-2610-00342."""
    return sinh_ma(cur, "KIEN_HANG", "MaKien", f"KI-{datetime.now():%y%m}-", 5)


# ------------------------------------------------------------------
# Khoi tao CSDL lan dau: tao database, chay schema + du lieu mau,
# tao tai khoan ung dung voi quyen toi thieu.
# ------------------------------------------------------------------
def _chay_script(cur, duong_dan: str) -> None:
    with open(duong_dan, encoding="utf-8") as f:
        noi_dung = f.read()
    for lo in re.split(r"^\s*GO\s*$", noi_dung, flags=re.MULTILINE):
        if lo.strip():
            cur.execute(lo)


def khoi_tao_csdl(so_lan_thu: int = 60) -> None:
    sa_pw = cfg.DB_SA_PASSWORD
    log.info("Trình điều khiển ODBC: %s", cfg.ODBC_DRIVER)
    for lan in range(1, so_lan_thu + 1):
        try:
            master = _mo(_chuoi_ket_noi("master", cfg.DB_SA_USER, sa_pw), autocommit=True)
            break
        except pyodbc.Error as e:
            log.info("Cho SQL Server san sang (%d/%d): %s", lan, so_lan_thu, e.args[0])
            time.sleep(3)
    else:
        raise RuntimeError("Khong ket noi duoc SQL Server")

    cur = master.cursor()
    cur.execute("SELECT DB_ID(?)", cfg.DB_NAME)
    if cur.fetchone()[0] is None:
        log.info("Tao database %s", cfg.DB_NAME)
        cur.execute(f"CREATE DATABASE [{cfg.DB_NAME}]")
    if not cfg.DB_TRUSTED:
        cur.execute("SELECT SUSER_ID(?)", cfg.DB_APP_USER)
        if cur.fetchone()[0] is None:
            mk = cfg.DB_APP_PASSWORD.replace("'", "''")
            cur.execute(f"CREATE LOGIN [{cfg.DB_APP_USER}] WITH PASSWORD = '{mk}', CHECK_POLICY = OFF")
    master.close()

    db = _mo(_chuoi_ket_noi(cfg.DB_NAME, cfg.DB_SA_USER, sa_pw), autocommit=True)
    cur = db.cursor()
    cur.execute("SELECT OBJECT_ID('kho.KHU')")
    if cur.fetchone()[0] is None:
        for ten in ("schema/01_schema.sql", "seed/02_seed.sql"):
            log.info("Chay %s", ten)
            _chay_script(cur, os.path.join(cfg.DB_SCRIPT_DIR, ten))
    if not cfg.DB_TRUSTED:
        cur.execute("SELECT USER_ID(?)", cfg.DB_APP_USER)
        if cur.fetchone()[0] is None:
            u = cfg.DB_APP_USER
            cur.execute(f"CREATE USER [{u}] FOR LOGIN [{u}]")
            cur.execute(f"ALTER ROLE r_ung_dung ADD MEMBER [{u}]")
            cur.execute(f"ALTER ROLE r_bao_cao ADD MEMBER [{u}]")
    db.close()
    log.info("CSDL san sang")
