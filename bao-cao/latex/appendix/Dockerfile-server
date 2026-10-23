# Tang Server: FastAPI + ODBC cho SQL Server
# Build context la goc repo (de chep ca thu muc db/ chua script CSDL)
#
# Trinh dieu khien ODBC:
#   - FreeTDS (tdsodbc) lay tu kho Debian -> luon cai duoc.
#   - "ODBC Driver 18 for SQL Server" cua Microsoft: thu cai them; neu mang chan
#     packages.microsoft.com thi bo qua, server tu dung FreeTDS (xem cau_hinh.py).
FROM python:3.12-slim-bookworm

# Kho Debian qua HTTPS (mot so mang/proxy chan hoac tra 503 cho HTTP cong 80), tu thu lai;
# neu deb.debian.org van loi thi doi sang may chu goc ftp.debian.org / security.debian.org.
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
 && printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' \
      > /etc/apt/apt.conf.d/80thu-lai \
 && ( apt-get update \
      || ( sed -i -e 's|https://deb.debian.org/debian-security|https://security.debian.org/debian-security|' \
                  -e 's|https://deb.debian.org|https://ftp.debian.org|g' /etc/apt/sources.list.d/debian.sources \
           && apt-get update ) ) \
 && apt-get install -y --no-install-recommends curl unixodbc tdsodbc \
 && rm -rf /var/lib/apt/lists/*

RUN ( curl -fsSL --retry 3 --connect-timeout 15 \
        https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb -o /tmp/ms.deb \
      && dpkg -i /tmp/ms.deb \
      && apt-get update \
      && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
      && echo ">>> Da cai ODBC Driver 18 for SQL Server" ) \
    || echo ">>> Khong tai duoc driver Microsoft, server se dung FreeTDS" ; \
    rm -rf /tmp/ms.deb /var/lib/apt/lists/*

WORKDIR /app/server
COPY server/requirements.txt .
# Mang cham: tang thoi gian cho va so lan thu; bo nho dem pip giu goi da tai giua cac lan build
ENV PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=10 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
COPY db /app/db
COPY server /app/server

ENV DB_SCRIPT_DIR=/app/db PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
