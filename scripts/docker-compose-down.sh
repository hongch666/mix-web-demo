#!/bin/bash

set -e

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$WORKDIR/docker-compose.yml"

# 查找可用的 compose 命令
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: docker-compose 或 Docker Compose CLI 未安装"
    exit 1
fi

cd "$WORKDIR"

# 默认只停容器、保留数据卷：日志（Loki）、链路（Tempo）、指标（Prometheus）与 Grafana
# 都落在命名卷上，重建容器不影响历史数据；确需清空时显式加 --volumes
REMOVE_VOLUMES=0
for arg in "$@"; do
    case $arg in
        -v|--volumes)
            REMOVE_VOLUMES=1
            ;;
    esac
done

if [ "$REMOVE_VOLUMES" = "1" ]; then
    echo "停止并删除 docker-compose 服务及数据卷..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down -v
else
    echo "停止并删除 docker-compose 服务（保留 loki/prometheus/tempo/grafana 数据卷）..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down
fi

# 清理 dev 模式残留的网关容器，避免下次启动报容器名冲突
bash "$WORKDIR/scripts/gateway-cleanup.sh"

if [ "$REMOVE_VOLUMES" = "1" ]; then
    echo "服务已停止，数据卷已删除"
else
    echo "服务已停止，数据卷保留（如需一并删除：./mix compose down --volumes）"
fi
