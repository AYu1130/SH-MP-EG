"""
ble_receiver.py
===============

BLE 接入适配器（基于 ``bleak``）。

功能
----
1. 周期扫描附近 BLE 广播，筛选名字前缀匹配 ``ble_name_prefixes`` 的设备；
2. 对匹配设备建立 GATT 连接，订阅 ``ble_notify_char_uuid`` 的 Notification；
3. 把收到的原始字节通过 :func:`data_converter.normalize_ble` 转为统一 JSON；
4. 断连自动重连，扫描失败有指数退避。

依赖
----
- Linux/RPi 推荐使用 BlueZ >= 5.55；
- Windows 调试时 bleak 会使用 WinRT 后端；
- 需要在 **异步环境** 下调用（使用 asyncio 事件循环）。

参考
----
- bleak 官方文档: https://bleak.readthedocs.io/
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Awaitable, Callable, Dict, Optional, Set

try:
    from bleak import BleakClient, BleakScanner  # type: ignore
    from bleak.backends.device import BLEDevice  # type: ignore
    _BLEAK_AVAILABLE = True
except ImportError:  # pragma: no cover - 取决于部署环境
    _BLEAK_AVAILABLE = False
    BleakClient = object  # type: ignore
    BleakScanner = object  # type: ignore
    BLEDevice = object  # type: ignore

from config import GatewayConfig
from data_converter import normalize_ble, validate
from logger import get_logger


logger = get_logger(__name__)

OnMessage = Callable[[Dict], None]
# 用于写回（下行命令）给 BLE 设备的回调；返回 True 表示成功
Writer = Callable[[str, bytes], Awaitable[bool]]


class BleReceiver:
    """BLE 适配器。管理扫描、连接、订阅、数据分发与下行写入。"""

    def __init__(self, cfg: GatewayConfig, on_message: OnMessage) -> None:
        self._cfg = cfg
        self._on_message = on_message
        self._stop_evt = asyncio.Event()

        # device_id -> BleakClient 映射，便于下行命令定位目标
        self._clients: Dict[str, BleakClient] = {}
        # 已在连接中的 MAC，避免重复连接同一设备
        self._connecting: Set[str] = set()
        # HM-10 / BT05 的 notify 每次最多 20 字节，长 JSON 会被拆成多次通知；
        # 用 device_id 维度的字节缓冲按 '\n' 重组完整帧
        self._rx_buffers: Dict[str, bytearray] = {}

    # ------------------------------------------------------------------ #
    # 公开入口
    # ------------------------------------------------------------------ #
    async def start(self) -> None:
        """启动扫描循环（作为后台 task 运行）。"""
        if not _BLEAK_AVAILABLE:
            logger.error("bleak 未安装，BLE 适配器无法启动。请 pip install bleak")
            return
        logger.info(
            "BleReceiver started: name_prefixes=%s interval=%.1fs",
            self._cfg.ble_name_prefixes,
            self._cfg.ble_scan_interval_s,
        )
        asyncio.create_task(self._scan_loop(), name="ble-scan-loop")

    async def stop(self) -> None:
        logger.info("stopping BleReceiver ...")
        self._stop_evt.set()
        for device_id, client in list(self._clients.items()):
            try:
                await client.disconnect()
            except Exception:
                pass
            self._clients.pop(device_id, None)
        logger.info("BleReceiver stopped")

    async def write(self, device_id: str, data: bytes) -> bool:
        """向指定 BLE 设备写入数据（下行命令）。

        设备必须处于连接中；成功返回 True，否则 False。
        """
        client = self._clients.get(device_id)
        if client is None or not client.is_connected:
            logger.warning("BLE write: device %s not connected", device_id)
            return False
        # HM-10/BT05 默认 ATT MTU 常见为 23，write-without-response 实际有效负载通常 <=20B。
        # 对超过 20B 的 JSON 命令做分片，避免 BlueZ "Failed to initiate write"。
        chunk_size = 20
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)] or [b""]
        try:
            for chunk in chunks:
                await client.write_gatt_char(
                    self._cfg.ble_notify_char_uuid, chunk, response=False
                )
            logger.info("BLE write -> %s: %s", device_id, data.hex())
            return True
        except Exception:
            logger.exception("BLE write failed for %s", device_id)
            return False

    # ------------------------------------------------------------------ #
    # 内部：扫描 / 连接 / 订阅
    # ------------------------------------------------------------------ #
    async def _scan_loop(self) -> None:
        """主扫描循环，直到 stop 事件触发。"""
        backoff = 1.0
        while not self._stop_evt.is_set():
            try:
                devices = await BleakScanner.discover(
                    timeout=self._cfg.ble_scan_interval_s,
                )
                backoff = 1.0  # 成功后复位退避
                for dev in devices:
                    if self._match(dev):
                        # 每个候选设备独立任务，避免相互阻塞
                        asyncio.create_task(
                            self._connect_and_subscribe(dev),
                            name=f"ble-conn-{dev.address}",
                        )
            except Exception:
                logger.exception("BLE scan failed, backoff=%.1fs", backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)

            # 与 scan interval 合并：若 scan 本身就 timeout 够久，可 sleep 短一些
            await asyncio.sleep(0.5)

    def _match(self, dev: BLEDevice) -> bool:
        """按 name 前缀过滤目标设备，并避免重复连接。"""
        name = (dev.name or "").strip()
        if not name:
            return False
        if not any(name.startswith(p) for p in self._cfg.ble_name_prefixes if p):
            return False
        if dev.address in self._connecting:
            return False
        device_id = self._device_id_of(dev)
        if device_id in self._clients and self._clients[device_id].is_connected:
            return False
        return True

    @staticmethod
    def _device_id_of(dev: BLEDevice) -> str:
        """用 name 或 MAC 派生一个稳定 device_id。"""
        return (dev.name or dev.address).replace(" ", "-")

    async def _connect_and_subscribe(self, dev: BLEDevice) -> None:
        """与单个 BLE 设备建立连接并订阅 notification。"""
        self._connecting.add(dev.address)
        device_id = self._device_id_of(dev)
        logger.info("BLE connecting: %s (%s)", dev.name, dev.address)

        client = BleakClient(dev)
        try:
            await client.connect(timeout=10.0)
            if not client.is_connected:
                logger.warning("BLE connect failed: %s", dev.address)
                return

            self._clients[device_id] = client

            # bleak notification 回调签名: (sender, data: bytearray) -> None
            # 为了兼容 HM-10 20B 分片，先把字节追加到 per-device 缓冲，
            # 再按 '\n' 切割成完整帧逐个 dispatch；无 '\n' 时走单帧语义。
            def _on_notify(_sender, data: bytearray) -> None:
                try:
                    buf = self._rx_buffers.setdefault(device_id, bytearray())
                    buf.extend(data)

                    # 防御：缓冲异常膨胀时丢弃前 1KB，避免 OOM
                    if len(buf) > 4096:
                        del buf[:1024]

                    if b"\n" in buf:
                        *complete, rest = buf.split(b"\n")
                        # rest 是还没收齐的尾巴，留回缓冲
                        buf.clear()
                        buf.extend(rest)
                        for frame in complete:
                            if not frame:
                                continue
                            msg = normalize_ble(
                                device_id=device_id,
                                raw_bytes=bytes(frame),
                                mac=dev.address,
                            )
                            if self._cfg.validate_schema:
                                validate(msg, strict=False)
                            self._on_message(msg)
                    else:
                        # 非 '\n' 分帧的情况：按单次 notify 作为一帧解析；
                        # 如果 payload 能单独解析通过就用掉缓冲
                        msg = normalize_ble(
                            device_id=device_id,
                            raw_bytes=bytes(buf),
                            mac=dev.address,
                        )
                        if msg.get("status") != "fault":
                            buf.clear()
                            if self._cfg.validate_schema:
                                validate(msg, strict=False)
                            self._on_message(msg)
                except Exception:
                    logger.exception("BLE on_notify handler error")

            await client.start_notify(self._cfg.ble_notify_char_uuid, _on_notify)
            logger.info("BLE subscribed: %s <- %s", device_id, self._cfg.ble_notify_char_uuid)
            # 连接建立后立即授时：STM32 用 sync_ns + millis() 外推 send_ns
            try:
                sync_cmd = json.dumps({"sync_ns": time.time_ns()}, separators=(",", ":")) + "\n"
                ok = await self.write(device_id, sync_cmd.encode("utf-8"))
                if not ok:
                    logger.warning("BLE sync_ns write failed for %s", device_id)
            except Exception:
                logger.exception("BLE sync_ns init failed for %s", device_id)

            # 保持连接，直到客户端断开或 stop
            while not self._stop_evt.is_set() and client.is_connected:
                await asyncio.sleep(1.0)

        except Exception:
            logger.exception("BLE connect/subscribe error for %s", dev.address)
        finally:
            self._connecting.discard(dev.address)
            try:
                await client.disconnect()
            except Exception:
                pass
            self._clients.pop(device_id, None)
            logger.info("BLE disconnected: %s", device_id)
