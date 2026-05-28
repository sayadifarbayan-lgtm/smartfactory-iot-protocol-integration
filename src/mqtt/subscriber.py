"""
Module 1 Assignment — Task 1.2
MQTT Wildcard Subscriber

Complete all TODO sections. Do not modify the function signatures.
"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
BROKER_HOST  = "localhost"
BROKER_PORT  = 1883
CLIENT_ID    = "smartfactory-subscriber-001"

TOPIC_ALL        = "factory/#"         # all factory messages
TOPIC_TEMP       = "factory/+/temperature"  # all temperature readings (any line)

CRITICAL_TEMP    = 85.0
SUMMARY_INTERVAL = 30   # seconds


class SmartFactorySubscriber:
    """Subscribes to SmartFactory sensor topics and processes incoming data."""

    def __init__(self, broker_host: str = BROKER_HOST, broker_port: int = BROKER_PORT):
        self.broker_host  = broker_host
        self.broker_port  = broker_port
        self._client      = mqtt.Client(client_id=CLIENT_ID, clean_session=False)
        self._msg_counts: dict[str, int] = defaultdict(int)
        self._last_summary = time.time()
        self._alerts_fired = 0

        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

    # ── Connection ─────────────────────────────────────────────────────────────

    def on_connect(self, client, userdata, flags: dict, rc: int) -> None:
        if rc == 0:
             log.info("Connected to broker")
             client.subscribe(TOPIC_ALL, qos=1)
             client.subscribe(TOPIC_TEMP, qos=2)
        else:
             log.error(f"Connection failure: {rc}")

    # ── Message Handling ───────────────────────────────────────────────────────

    def on_message(self, client, userdata, msg: mqtt.MQTTMessage) -> None:
        self._msg_counts[msg.topic] += 1

        try:
             payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            payload = msg.payload.decode("utf-8", errors="replace")

        self._print_message(msg, payload)

        if msg.topic.endswith("/temperature"):
             self._check_temperature_alert(msg.topic, payload)

        now = time.time()
        if now - self._last_summary >= SUMMARY_INTERVAL:
            self._print_summary()
            self._last_summary = now

    def _print_message(self, msg: mqtt.MQTTMessage, payload: Any) -> None:
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")

        if isinstance(payload, dict) and "value" in payload:
            unit = payload.get("unit", "")
            value_text = f"{payload['value']} {unit}".strip()
        else:
            value_text = str(payload)

        print(
            f"[{now}] {msg.topic}  "
            f"val={value_text}  "
            f"QoS={msg.qos}  "
            f"retain={msg.retain}"
        )

    def _check_temperature_alert(self, topic: str, payload: Any) -> None:
        if not isinstance(payload, dict):
            return

        value = payload.get("value")
        if value is None:
            return

        try:
            value = float(value)
        except (TypeError, ValueError):
            return

        if value > CRITICAL_TEMP:
            self._alerts_fired += 1
            timestamp = payload.get("timestamp", datetime.now(timezone.utc).isoformat())

            print("╔══════════════════════════════════════╗")
            print(f"║  ⚠ CRITICAL ALERT — {topic}")
            print(f"║  Temperature: {value}°C  (threshold: {CRITICAL_TEMP}°C)")
            print(f"║  Time: {timestamp}")
            print("╚══════════════════════════════════════╝")

    def _print_summary(self) -> None:
        total = sum(self._msg_counts.values())

        print("── Message Summary ──────────────────────")
        for topic, count in sorted(self._msg_counts.items()):
            print(f"{topic:<50}  {count:>6} msgs")
        print(f"Total: {total} messages  |  Alerts fired: {self._alerts_fired}")
        print("────────────────────────────────────────")

    # ── Run ────────────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Connect and block until interrupted."""
        self._client.connect(self.broker_host, self.broker_port, keepalive=60)
        log.info("Listening for messages (Ctrl-C to stop)")
        try:
            self._client.loop_forever()
        except KeyboardInterrupt:
            log.info("Subscriber stopped")
        finally:
            self._client.disconnect()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sub = SmartFactorySubscriber()
    sub.run()
