"""
data_converter.py
=================

协议转换与数据融合模块。

本文件提供 **统一 JSON 数据模型** 的构造与校验：
    {
        "device_id":   str,
        "device_type": str,  # 例如 wifi / ble / zigbee
        "transport":   str,  # 例如 tcp / http / ble / mqtt
        "timestamp":   int,  # Unix 秒
        "status":      str,  # online / offline / fault
        "payload":     {...} # 业务测量字段
    }

- ``normalize_wifi()`` / ``normalize_ble()``：把各协议适配器原始解析结果
  转成统一模型；
- ``validate()``：使用 ``jsonschema`` 做格式校验（可选）；
- ``UNIFIED_SCHEMA``：即 ``docs/interfaces/json_schema.md`` 的 Python 镜像。
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

try:
    # jsonschema 为可选依赖；若未安装则校验退化为简单的字段检查
    from jsonschema import Draft202012Validator  # type: ignore
    _JSONSCHEMA_AVAILABLE = True
except ImportError:  # pragma: no cover - 取决于环境
    _JSONSCHEMA_AVAILABLE = False

from logger import get_logger


logger = get_logger(__name__)


# --------------------------------------------------------------------------- #
# 统一 JSON Schema（与 docs/interfaces/json_schema.md 保持一致）
# --------------------------------------------------------------------------- #
UNIFIED_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "GatewayUnifiedMessage",
    "type": "object",
    "required": [
        "device_id",
        "device_type",
        "transport",
        "timestamp",
        "status",
        "payload",
    ],
    "properties": {
        "device_id": {"type": "string", "minLength": 1},
        "device_type": {"type": "string", "minLength": 1},
        "transport": {"type": "string", "minLength": 1},
        "timestamp": {"type": "integer", "minimum": 0},
        "status": {"type": "string", "enum": ["online", "offline", "fault"]},
        "payload": {
            "type": "object",
            "properties": {
                "temperature": {"type": "number"},
                "humidity": {"type": "number"},
                "light": {"type": "number"},
                "battery": {"type": "number"},
                "co2": {"type": "number"},
                "pm25": {"type": "number"},
            },
            "additionalProperties": True,
        },
    },
    "additionalProperties": True,
}

_VALIDATOR = Draft202012Validator(UNIFIED_SCHEMA) if _JSONSCHEMA_AVAILABLE else None


# --------------------------------------------------------------------------- #
# 核心构造函数
# --------------------------------------------------------------------------- #
def build_unified_message(
    device_id: str,
    device_type: str,
    transport: str,
    payload: Dict[str, Any],
    status: str = "online",
    timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """构造符合统一 JSON Schema 的消息。

    Parameters
    ----------
    device_id : str
        设备唯一标识，建议格式 ``<type>-<seq>``，例如 ``esp32-s3-node-01``。
    device_type : str
        设备类型标签，例如 ``wifi`` / ``ble`` / ``zigbee``。
    transport : str
        实际传输协议，例如 ``tcp`` / ``http`` / ``ble``。
    payload : dict
        业务测量字段，键名建议使用小写蛇形，例如 ``temperature``。
    status : str
        设备状态，默认 ``online``。
    timestamp : Optional[int]
        Unix 秒；未提供时取当前时间。
    """
    return {
        "device_id": device_id,
        "device_type": device_type,
        "transport": transport,
        "timestamp": int(timestamp if timestamp is not None else time.time()),
        "status": status,
        "payload": payload,
    }


# --------------------------------------------------------------------------- #
# 校验
# --------------------------------------------------------------------------- #
def validate(message: Dict[str, Any], strict: bool = True) -> bool:
    """校验统一 JSON 消息是否合法。

    - 若安装了 ``jsonschema``，使用 Draft 2020-12 标准校验；
    - 否则退化为最小字段检查。

    ``strict=True`` 时校验失败抛出 ``ValueError``，否则仅返回 ``False``。
    """
    if _VALIDATOR is not None:
        errors = sorted(_VALIDATOR.iter_errors(message), key=lambda e: e.path)
        if errors:
            detail = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
            if strict:
                raise ValueError(f"unified message schema invalid: {detail}")
            logger.warning("schema validation failed: %s", detail)
            return False
        return True

    # fallback：最小字段检查
    required = {"device_id", "device_type", "transport", "timestamp", "status", "payload"}
    missing = required - set(message.keys())
    if missing:
        if strict:
            raise ValueError(f"unified message missing fields: {missing}")
        logger.warning("unified message missing fields: %s", missing)
        return False
    return True


# --------------------------------------------------------------------------- #
# 协议 -> 统一 JSON 适配
# --------------------------------------------------------------------------- #
def normalize_wifi(raw: Dict[str, Any], transport: str = "http") -> Dict[str, Any]:
    """把 Wi-Fi 节点上报的原始 JSON 转换成统一模型。

    约定原始报文示例::

        {
            "id": "esp32-s3-node-01",
            "t": 25.4, "h": 56.1, "l": 534,
            "ts": 1713333333      # 可选；无则用网关时间
        }

    - 支持短字段名（``t/h/l/ts``）与长字段名（``temperature``...）并存；
    - 未识别字段原样写入 ``payload``，方便后续扩展。
    """
    device_id = str(raw.get("id") or raw.get("device_id") or "unknown-wifi")

    payload: Dict[str, Any] = {}
    # 短 -> 长的字段映射表
    alias_map = {
        "t": "temperature",
        "h": "humidity",
        "l": "light",
        "b": "battery",
    }
    reserved = {"id", "device_id", "ts", "timestamp", "status", "type", "device_type"}
    for k, v in raw.items():
        if k in reserved:
            continue
        key = alias_map.get(k, k)
        payload[key] = v

    return build_unified_message(
        device_id=device_id,
        device_type="wifi",
        transport=transport,
        payload=payload,
        status=str(raw.get("status", "online")),
        timestamp=int(raw["ts"]) if "ts" in raw else None,
    )


def normalize_ble(
    device_id: str,
    raw_bytes: bytes,
    mac: Optional[str] = None,
) -> Dict[str, Any]:
    """把 BLE GATT 通知的原始字节转成统一 JSON。

    支持两种常见编码：
    1. **ASCII JSON**（HM-10/ESP32 透传模式）：直接 ``json.loads``；
    2. **自定义二进制帧**（固定 5 字节，预留）：
       - byte 0: 0xA5 (Magic)
       - byte 1: device id low
       - byte 2-3: light value (big-endian uint16)
       - byte 4: checksum (前 4 字节求和 & 0xFF)
       若校验通过，映射成 ``{"light": <value>}``。

    任一方式解析失败时，把原始字节 base16 字符串放入 payload 的 ``raw_hex``
    字段，便于排障。
    """
    # ---- 方式 1：尝试当作 UTF-8 JSON 字符串 ------------------------------
    try:
        text = raw_bytes.decode("utf-8").strip()
        obj = json.loads(text)
        if isinstance(obj, dict):
            if mac and "mac" not in obj:
                obj["mac"] = mac
            payload = {k: v for k, v in obj.items() if k not in ("ts", "timestamp", "status", "id")}
            return build_unified_message(
                device_id=str(obj.get("id", device_id)),
                device_type="ble",
                transport="ble",
                payload=payload,
                status=str(obj.get("status", "online")),
                timestamp=int(obj["ts"]) if "ts" in obj else None,
            )
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass  # 继续尝试二进制帧

    # ---- 方式 2：自定义二进制帧 -----------------------------------------
    if len(raw_bytes) == 5 and raw_bytes[0] == 0xA5:
        checksum = sum(raw_bytes[:4]) & 0xFF
        if checksum == raw_bytes[4]:
            light = int.from_bytes(raw_bytes[2:4], "big")
            payload = {"light": light}
            if mac:
                payload["mac"] = mac
            return build_unified_message(
                device_id=device_id,
                device_type="ble",
                transport="ble",
                payload=payload,
            )

    # ---- 兜底：透传原始字节 ---------------------------------------------
    logger.warning("BLE raw bytes cannot be parsed, fallback to raw_hex: %s", raw_bytes.hex())
    payload = {"raw_hex": raw_bytes.hex()}
    if mac:
        payload["mac"] = mac
    return build_unified_message(
        device_id=device_id,
        device_type="ble",
        transport="ble",
        payload=payload,
        status="fault",
    )


# --------------------------------------------------------------------------- #
# 便捷序列化
# --------------------------------------------------------------------------- #
def to_json(message: Dict[str, Any]) -> str:
    """把统一消息序列化为紧凑 JSON 字符串，用于 MQTT 发布。"""
    return json.dumps(message, ensure_ascii=False, separators=(",", ":"))
