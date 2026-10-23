# Tang Web app: Streamlit, chi goi REST API cua tang Server
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY webapp/requirements.txt .
# Mang cham: tang thoi gian cho va so lan thu; bo nho dem pip giu goi da tai giua cac lan build
ENV PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=10 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
COPY webapp /app
ENV PYTHONUNBUFFERED=1
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]
