"""
config.py
=========

网关全局配置模块。

设计说明
--------
1. 所有可调参数集中在 ``GatewayConfig`` dataclass 中，便于统一管理与测试
   mock；
2. 支持三种配置来源，优先级从高到低：
   命令行参数 > 环境变量 > 文件默认值；
3. 环境变量前缀统一为 ``SHMPEG_``，例如 ``SHMPEG_MQTT_HOST``；
4. 任何新增配置项都应带有 *类型注解* 与 *默认值*，以保证
   ``python main.py --help`` 输出的可读性和 IDE 提示。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from typing import List


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def _env(key: str, default: str) -> str:
    """读取带前缀的环境变量，未设置则返回默认值。"""
    return os.environ.get(f"SHMPEG_{key}", default)


def _env_int(key: str, default: int) -> int:
    return int(_env(key, str(default)))


def _env_bool(key: str, default: bool) -> bool:
    return _env(key, "1" if default else "0").lower() in ("1", "true", "yes", "on")


# --------------------------------------------------------------------------- #
# 主配置 dataclass
# --------------------------------------------------------------------------- #
@dataclass
class GatewayConfig:
    """网关运行参数。字段按模块分组。"""

    # ----- 通用 --------------------------------------------------------------
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))
    log_file: str = field(default_factory=lambda: _env("LOG_FILE", "logs/gateway.log"))

    # ----- Wi-Fi 接入适配器 --------------------------------------------------
    wifi_enabled: bool = field(default_factory=lambda: _env_bool("WIFI_ENABLED", True))
    wifi_host: str = field(default_factory=lambda: _env("WIFI_HOST", "0.0.0.0"))
    wifi_http_port: int = field(default_factory=lambda: _env_int("WIFI_HTTP_PORT", 8080))
    wifi_tcp_port: int = field(default_factory=lambda: _env_int("WIFI_TCP_PORT", 9000))

    # ----- BLE 接入适配器 ---------------------------------------------------
    ble_enabled: bool = field(default_factory=lambda: _env_bool("BLE_ENABLED", True))
    # 允许匹配的 BLE 设备名前缀，例如 HM-10 默认名 "BT05" 或自定义 "SHMPEG-"
    ble_name_prefixes: List[str] = field(
        default_factory=lambda: _env("BLE_NAME_PREFIXES", "SHMPEG-,BT05,HMSoft").split(",")
    )
    ble_scan_interval_s: float = field(
        default_factory=lambda: float(_env("BLE_SCAN_INTERVAL_S", "5.0"))
    )
    # GATT Characteristic UUID（Nordic UART Service，HM-10 常用 FFE0/FFE1）
    ble_notify_char_uuid: str = field(
        default_factory=lambda: _env("BLE_NOTIFY_CHAR_UUID", "0000ffe1-0000-1000-8000-00805f9b34fb")
    )

    # ----- MQTT 本地代理 -----------------------------------------------------
    mqtt_host: str = field(default_factory=lambda: _env("MQTT_HOST", "127.0.0.1"))
    mqtt_port: int = field(default_factory=lambda: _env_int("MQTT_PORT", 1883))
    mqtt_username: str = field(default_factory=lambda: _env("MQTT_USERNAME", ""))
    mqtt_password: str = field(default_factory=lambda: _env("MQTT_PASSWORD", ""))
    mqtt_client_id: str = field(default_factory=lambda: _env("MQTT_CLIENT_ID", "shmpeg-gateway"))
    mqtt_keepalive: int = field(default_factory=lambda: _env_int("MQTT_KEEPALIVE", 30))
    mqtt_qos: int = field(default_factory=lambda: _env_int("MQTT_QOS", 1))

    # ----- Topic 规范(见 docs/interfaces/mqtt_topics.md) ---------------------
    # smarthome/v1/<domain>/<device_type>/<device_id>
    topic_prefix: str = field(default_factory=lambda: _env("TOPIC_PREFIX", "smarthome/v1"))

    # ----- 本地缓存 (SQLite) -------------------------------------------------
    cache_enabled: bool = field(default_factory=lambda: _env_bool("CACHE_ENABLED", True))
    cache_db_path: str = field(default_factory=lambda: _env("CACHE_DB_PATH", "data/cache.db"))
    cache_retry_interval_s: float = field(
        default_factory=lambda: float(_env("CACHE_RETRY_INTERVAL_S", "10.0"))
    )
    cache_max_rows: int = field(default_factory=lambda: _env_int("CACHE_MAX_ROWS", 100_000))

    # ----- 校验配置 ----------------------------------------------------------
    validate_schema: bool = field(default_factory=lambda: _env_bool("VALIDATE_SCHEMA", True))

    # ----- Web 管理（用户 / 节点，SQLite + Flask Session）--------------------
    admin_enabled: bool = field(default_factory=lambda: _env_bool("ADMIN_ENABLED", True))
    admin_db_path: str = field(default_factory=lambda: _env("ADMIN_DB_PATH", "data/admin.db"))
    # Flask session 密钥；生产务必通过环境变量覆盖
    admin_secret_key: str = field(
        default_factory=lambda: _env("ADMIN_SECRET_KEY", "shmpeg-dev-change-me")
    )
    # 首次建库时若不存在任何用户，则创建该管理员（仅当设置了非空密码时写入）；
    # 默认在代码中提供占位，仍建议部署后立刻修改密码。
    admin_bootstrap_username: str = field(
        default_factory=lambda: _env("ADMIN_BOOTSTRAP_USERNAME", "admin")
    )
    admin_bootstrap_password: str = field(
        default_factory=lambda: _env("ADMIN_BOOTSTRAP_PASSWORD", "admin")
    )
    # 超过该秒数未收到上行 telemetry 则管理台视为离线
    admin_online_grace_sec: float = field(
        default_factory=lambda: float(_env("ADMIN_ONLINE_GRACE_SEC", "120"))
    )

    # ----------------------------------------------------------------------- #
    # 便捷方法
    # ----------------------------------------------------------------------- #
    def telemetry_topic(self, device_type: str, device_id: str) -> str:
        """生成上行 telemetry 主题。"""
        return f"{self.topic_prefix}/telemetry/{device_type}/{device_id}"

    def status_topic(self, device_type: str, device_id: str) -> str:
        """生成设备状态事件主题。"""
        return f"{self.topic_prefix}/status/{device_type}/{device_id}"

    def command_topic(self, device_type: str, device_id: str) -> str:
        """生成下行命令主题（网关订阅，转发到具体协议）。"""
        return f"{self.topic_prefix}/command/{device_type}/{device_id}"

    def command_topic_wildcard(self) -> str:
        """订阅所有下行命令使用的通配符主题。"""
        return f"{self.topic_prefix}/command/+/+"

    def to_dict(self) -> dict:
        """方便打印 / 写日志。"""
        return asdict(self)


# --------------------------------------------------------------------------- #
# 模块级默认实例（main.py 通过 argparse 覆盖后再使用）
# --------------------------------------------------------------------------- #
DEFAULT_CONFIG = GatewayConfig()
