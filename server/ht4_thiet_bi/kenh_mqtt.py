"""Ket noi MQTT cua tang Server (Mosquitto, OASIS MQTT v3.1.1/5.0).

clean_session=False voi client id co dinh: broker giu ban tin QoS 1 trong luc
server ngung, giao lai khi server ket noi lai.
"""
import json
import logging

import paho.mqtt.client as mqtt

import cau_hinh as cfg
from ht4_thiet_bi.tiep_nhan import BoTiepNhan

log = logging.getLogger(__name__)

CHU_DE_DANG_KY = [("kho/thietbi/+/doc-the", 1), ("kho/thietbi/+/trang-thai", 1),
                  ("kho/agv/+/nhiem-vu", 1)]


class KenhMQTT:
    def __init__(self, bo_tiep_nhan: BoTiepNhan):
        self.bo = bo_tiep_nhan
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="kho-server",
                                  clean_session=False, protocol=mqtt.MQTTv311)
        self.client.username_pw_set(cfg.MQTT_USER, cfg.MQTT_PASSWORD)
        self.client.on_connect = self._khi_ket_noi
        self.client.on_message = self._khi_nhan
        self.client.on_disconnect = lambda c, u, f, rc, p: log.warning("Mất kết nối MQTT: %s", rc)

    def _khi_ket_noi(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("Kết nối MQTT thất bại: %s", reason_code)
            return
        client.subscribe(CHU_DE_DANG_KY)
        log.info("Đã kết nối MQTT broker, đăng ký %d chủ đề", len(CHU_DE_DANG_KY))

    def _khi_nhan(self, client, userdata, msg):
        kq = self.bo.tiep_nhan(msg.topic, msg.payload)
        log.info("%s -> %s", msg.topic, kq)

    def bat_dau(self):
        self.client.connect_async(cfg.MQTT_HOST, cfg.MQTT_PORT, keepalive=30)
        self.client.loop_start()

    def dung(self):
        self.client.loop_stop()
        self.client.disconnect()

    def phat(self, chu_de: str, du_lieu: dict) -> None:
        self.client.publish(chu_de, json.dumps(du_lieu, ensure_ascii=False, default=str), qos=1)
