FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV ROBOT_ID=robot-01 \
    MQTT_HOST=mosquitto \
    MQTT_PORT=1883 \
    PUBLISH_HZ=20

CMD ["python", "-u", "main.py"]
