FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "Flask>=3.0,<4"
COPY app.py .
EXPOSE 8081
CMD ["python", "app.py"]
