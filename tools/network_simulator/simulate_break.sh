#!/usr/bin/env bash
# =============================================================================
# simulate_break.sh
# -----------------------------------------------------------------------------
# 在 Linux 上临时阻断 / 恢复网关与 MQTT Broker 的连接，用于验证
# "断网恢复 + 本地缓存补传" 需求。
#
# 使用方式:
#   sudo ./simulate_break.sh break   <mqtt_host>   -- 阻断出流量
#   sudo ./simulate_break.sh restore <mqtt_host>   -- 恢复
#
#   sudo ./simulate_break.sh loss  30              -- 使用 tc 模拟 30% 丢包
#   sudo ./simulate_break.sh delay 200             -- 使用 tc 模拟 200ms 延迟
#   sudo ./simulate_break.sh clear                 -- 清除所有 tc 规则
#
# 依赖: iptables / tc (iproute2)。需要 root 权限。
# 实测网卡默认为 eth0，需要时用 IFACE=wlan0 ./simulate_break.sh ... 覆盖。
# =============================================================================
set -euo pipefail

IFACE="${IFACE:-eth0}"

usage() {
  grep '^#' "$0" | sed -e 's/^# \{0,1\}//'
  exit 1
}

cmd="${1:-}"
arg="${2:-}"

case "$cmd" in
  break)
    [ -z "$arg" ] && usage
    echo "[+] blocking outbound to $arg on $IFACE"
    iptables -I OUTPUT -p tcp -d "$arg" -j DROP
    ;;

  restore)
    [ -z "$arg" ] && usage
    echo "[+] removing block to $arg"
    iptables -D OUTPUT -p tcp -d "$arg" -j DROP || true
    ;;

  loss)
    [ -z "$arg" ] && usage
    echo "[+] adding ${arg}% random packet loss on $IFACE"
    tc qdisc replace dev "$IFACE" root netem loss "${arg}%"
    ;;

  delay)
    [ -z "$arg" ] && usage
    echo "[+] adding ${arg}ms delay on $IFACE"
    tc qdisc replace dev "$IFACE" root netem delay "${arg}ms"
    ;;

  clear)
    echo "[+] clearing tc qdisc on $IFACE"
    tc qdisc del dev "$IFACE" root || true
    ;;

  *)
    usage
    ;;
esac
