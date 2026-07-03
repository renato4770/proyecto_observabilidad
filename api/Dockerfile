FROM python:3.12-slim

WORKDIR /app

# setuptools ya no viene incluido en Python 3.12, hay que instalarlo explícitamente
RUN pip install --no-cache-dir setuptools

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]