#!/bin/sh
# Tao tai khoan MQTT tu bien moi truong roi khoi chay broker.
set -e
P=/mosquitto/data/passwd
: > "$P"
mosquitto_passwd -b "$P" server "$MQTT_SERVER_PASSWORD"
for tb in GT-01 GT-02 HH-01 AGV-01 AGV-02; do
  mosquitto_passwd -b "$P" "$tb" "$MQTT_DEVICE_PASSWORD"
done
chown mosquitto:mosquitto "$P" 2>/dev/null || true
chmod 0700 "$P"
exec mosquitto -c /mosquitto/config/mosquitto.conf
