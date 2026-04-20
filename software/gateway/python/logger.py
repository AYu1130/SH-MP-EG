"""
logger.py
=========

统一日志工具。

- 控制台彩色输出 + 轮转文件输出；
- 所有模块统一通过 ``get_logger(__name__)`` 获取 logger；
- 日志级别、文件路径由 ``config.GatewayConfig`` 控制。

日志文件默认位于 ``software/gateway/python/logs/gateway.log``，
按 5MB 分割保留 5 份。
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from typing import Optional


# --------------------------------------------------------------------------- #
# 颜色化 Formatter（仅控制台使用；文件日志保持纯文本便于 grep）
# --------------------------------------------------------------------------- #
class _ColorFormatter(logging.Formatter):
    """为不同日志级别添加 ANSI 颜色。"""

    # 常见 ANSI color code
    _COLORS = {
        "DEBUG": "\033[36m",     # 青色
        "INFO": "\033[32m",      # 绿色
        "WARNING": "\033[33m",   # 黄色
        "ERROR": "\033[31m",     # 红色
        "CRITICAL": "\033[1;31m",  # 粗体红色
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._COLORS.get(record.levelname, "")
        message = super().format(record)
        return f"{color}{message}{self._RESET}" if color else message


_DEFAULT_FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

# 避免 basicConfig 被重复执行导致输出重复
_initialized = False


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "logs/gateway.log",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """初始化全局 logging 配置。

    Parameters
    ----------
    level : str
        日志级别字符串，例如 ``"INFO"`` / ``"DEBUG"``。
    log_file : Optional[str]
        日志文件路径，传入 None 则只输出到控制台。
    max_bytes : int
        单个日志文件最大字节数。
    backup_count : int
        保留的历史文件份数。
    """
    global _initialized
    if _initialized:
        return

    root = logging.getLogger()
    root.setLevel(level.upper())
    # 清理旧 handler，避免在 reload 场景下重复挂载
    for h in list(root.handlers):
        root.removeHandler(h)

    # 控制台 handler ------------------------------------------------------- #
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(_ColorFormatter(_DEFAULT_FMT, _DEFAULT_DATEFMT))
    root.addHandler(console)

    # 文件 handler --------------------------------------------------------- #
    if log_file:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(_DEFAULT_FMT, _DEFAULT_DATEFMT))
        root.addHandler(file_handler)

    _initialized = True
    logging.getLogger(__name__).debug("logging initialized: level=%s file=%s", level, log_file)


def get_logger(name: str) -> logging.Logger:
    """子模块获取 logger 的唯一入口。"""
    if not _initialized:
        # 允许在 setup_logging 之前被调用，使用 INFO 的控制台默认输出
        setup_logging()
    return logging.getLogger(name)
