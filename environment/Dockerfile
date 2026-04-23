FROM python:3.12.4-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir fakeredis

EXPOSE 5000

CMD ["python", "run.py"]