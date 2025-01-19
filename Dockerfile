FROM python:latest

WORKDIR /app

COPY wildfire_proxy.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 1025

CMD ["python", "wildfire_proxy.py"]
