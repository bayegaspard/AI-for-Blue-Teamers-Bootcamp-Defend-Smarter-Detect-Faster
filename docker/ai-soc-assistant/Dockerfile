FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "Flask>=3.0,<4"
COPY app.py .
COPY alerts.json .
COPY templates ./templates
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
CMD ["python", "app.py"]
