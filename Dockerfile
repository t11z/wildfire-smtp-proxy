FROM ubuntu:24.04

WORKDIR /app

COPY wildfire_proxy.py .

RUN apt-get update && \
  apt-get install -y python3 python3-pip && \
  pip3 install --no-cache-dir -r requirements.txt && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

EXPOSE 1025

CMD ["python3", "wildfire_proxy.py"]