# =============================================================================
# SH-MP-EG Gateway Python 容器镜像
# -----------------------------------------------------------------------------
# 用途: 把 gateway 网关程序封装为可移植容器（不含 EMQX；EMQX 单独部署）。
#
# 构建:
#   docker build -f docs/deployment/docker/Dockerfile -t shmpeg/gateway:dev .
# 运行:
#   docker run -d --name shmpeg-gw \
#     --network host \
#     --device /dev/ttyUSB0 \
#     -e SHMPEG_MQTT_HOST=127.0.0.1 \
#     shmpeg/gateway:dev
#
# 注意: BLE 需要宿主机 BlueZ 支持，建议 host 网络 + privileged 运行。
# =============================================================================
FROM python:3.11-slim AS base

# 系统依赖：bleak 使用 dbus / bluetooth 栈
RUN apt-get update && apt-get install -y --no-install-recommends \
        bluez \
        libglib2.0-0 \
        build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先只拷贝 requirements，避免代码变动导致重新下载依赖
COPY software/gateway/python/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝源码
COPY software/gateway/python/ ./

# 默认读取环境变量配置
ENV PYTHONUNBUFFERED=1 \
    SHMPEG_MQTT_HOST=127.0.0.1 \
    SHMPEG_MQTT_PORT=1883

EXPOSE 8080 9000

CMD ["python", "main.py"]
