FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "PyMySQL>=1.1,<2"
COPY src /app/src
COPY mock_server /app/mock_server
ENV PYTHONPATH=/app/src:/app
CMD ["python", "-m", "rahkaran_integration.main"]
