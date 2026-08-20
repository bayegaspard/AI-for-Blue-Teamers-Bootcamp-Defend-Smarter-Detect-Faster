FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "Flask>=3.0,<4"
COPY app.py .
EXPOSE 11434
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:11434/health'); " || exit 1
CMD ["python", "app.py"]
