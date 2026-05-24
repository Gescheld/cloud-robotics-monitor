"""Subscribe once and print a few telemetry messages (local dev helper)."""

import json
import os
import sys

import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "robots/+/telemetry")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "5"))


def main() -> None:
    count = 0

    def on_message(_client, _userdata, msg):
        nonlocal count
        count += 1
        data = json.loads(msg.payload.decode())
        print(f"{msg.topic}: error_code={data.get('error_code')} joints={data.get('joint_positions')[:2]}...")
        if count >= MAX_MESSAGES:
            _client.disconnect()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(HOST, PORT)
    client.subscribe(TOPIC)
    print(f"Listening on {HOST}:{PORT} {TOPIC} (max {MAX_MESSAGES} messages)...")
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
