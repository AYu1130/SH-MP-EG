"""
数据转换层单元测试。

- 不依赖运行中的网关 / Broker；
- 覆盖 Wi-Fi / BLE 两类输入 + schema 校验边界情况。
"""

from __future__ import annotations

import json
import time

import pytest

from data_converter import (
    build_unified_message,
    normalize_ble,
    normalize_wifi,
    to_json,
    validate,
)


# ------------------------------------------------------------------ Wi-Fi -- #
class TestNormalizeWifi:

    def test_short_field_alias_mapping(self):
        raw = {"id": "esp32-s3-node-01", "t": 25.4, "h": 56.1, "l": 534}
        msg = normalize_wifi(raw)
        assert msg["device_id"] == "esp32-s3-node-01"
        assert msg["device_type"] == "wifi"
        assert msg["transport"] == "http"  # 默认
        assert msg["payload"]["temperature"] == 25.4
        assert msg["payload"]["humidity"] == 56.1
        assert msg["payload"]["light"] == 534
        validate(msg)  # 不抛异常即通过

    def test_long_field_passthrough(self):
        raw = {"id": "node-42", "temperature": 10, "custom_metric": 7}
        msg = normalize_wifi(raw)
        assert msg["payload"]["temperature"] == 10
        assert msg["payload"]["custom_metric"] == 7

    def test_timestamp_override_and_default(self):
        before = int(time.time())
        msg_default = normalize_wifi({"id": "x"})
        after = int(time.time())
        assert before <= msg_default["timestamp"] <= after + 1

        msg_fixed = normalize_wifi({"id": "x", "ts": 1_700_000_000})
        assert msg_fixed["timestamp"] == 1_700_000_000

    def test_unknown_id_fallback(self):
        msg = normalize_wifi({"t": 1})
        assert msg["device_id"] == "unknown-wifi"


# -------------------------------------------------------------------- BLE -- #
class TestNormalizeBle:

    def test_ascii_json_notification(self):
        raw = b'{"id":"ble-node-01","light":321}'
        msg = normalize_ble("ble-node-01", raw, mac="AA:BB:CC:DD:EE:FF")
        assert msg["device_id"] == "ble-node-01"
        assert msg["device_type"] == "ble"
        assert msg["payload"]["light"] == 321
        assert msg["payload"]["mac"] == "AA:BB:CC:DD:EE:FF"

    def test_binary_frame_parse(self):
        # magic 0xA5 + id + uint16 light(0x0141=321) + checksum
        body = bytes([0xA5, 0x01, 0x01, 0x41])
        checksum = sum(body) & 0xFF
        raw = body + bytes([checksum])
        msg = normalize_ble("ble-node-02", raw)
        assert msg["payload"]["light"] == 0x0141

    def test_bad_frame_fallback(self):
        raw = b"\x01\x02\x03"
        msg = normalize_ble("ble-node-03", raw)
        assert msg["status"] == "fault"
        assert msg["payload"]["raw_hex"] == raw.hex()


# -------------------------------------------------------------- validation - #
class TestValidate:

    def test_build_unified_message_shape(self):
        msg = build_unified_message("a", "wifi", "http", {"temperature": 1})
        assert validate(msg) is True

    def test_missing_required_strict(self):
        bad = {"device_id": "a"}
        with pytest.raises(ValueError):
            validate(bad, strict=True)

    def test_missing_required_nonstrict(self):
        bad = {"device_id": "a"}
        assert validate(bad, strict=False) is False

    def test_to_json_is_compact(self):
        msg = build_unified_message("a", "wifi", "http", {"t": 1})
        s = to_json(msg)
        assert " " not in s.replace('" ', '"').replace(' "', '"')  # 无多余空格
        parsed = json.loads(s)
        assert parsed["device_id"] == "a"
