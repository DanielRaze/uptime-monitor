FROM python:3.12-slim

WORKDIR /app

RUN useradd -u 8888 appuser

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

RUN mkdir -p /data && chown appuser:appuser /data

USER appuser

EXPOSE 8000

ENTRYPOINT ["python"]
CMD ["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
