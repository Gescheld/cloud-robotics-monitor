FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py models.py ./

ENV MQTT_HOST=mosquitto \
    MQTT_PORT=1883 \
    MQTT_TOPIC=robots/+/telemetry \
    POSTGRES_URL=postgresql://robotics:robotics@postgres:5432/telemetry \
    BATCH_INTERVAL_S=0.5 \
    BATCH_SIZE=100

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
