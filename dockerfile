FROM python:3.11-slim AS builder

WORKDIR /install


COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --prefix=/install/packages \
        --no-cache-dir \
        -r requirements.txt



FROM python:3.11-slim

# Metadata
LABEL maintainer="paperlens"
LABEL description="PaperLens — Flask + LangChain + Groq"


WORKDIR /PaperLens


COPY --from=builder /install/packages /usr/local


COPY requirements.txt    .
COPY .gitignore          .
COPY main.py             .

COPY fetcher/            ./fetcher/
COPY utils/              ./utils/
COPY summarizer/         ./summarizer/
COPY explainer/          ./explainer/
COPY app/                ./app/


RUN mkdir -p outputs/summaries


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production


EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1


CMD ["gunicorn", \
     "--workers", "2", \
     "--threads", "2", \
     "--timeout", "120", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.app:app"]