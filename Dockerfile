FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN useradd -m appuser
WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .env.sample ./.env.sample
COPY start.sh /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh \
 && sed -i '1s/^\xEF\xBB\xBF//' /app/start.sh \
 && chmod +x /app/start.sh
ENTRYPOINT ["/bin/sh", "/app/start.sh"]


RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "/app/start.sh"]
