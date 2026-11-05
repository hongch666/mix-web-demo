#!/bin/bash

# 脚本说明：dev 模式启动 APISIX 网关
#
# 背景：`docker compose up` 创建容器的瞬间，APISIX 的 Nacos 发现模块会并发拉取各服务实例，
#   此时容器网络可能尚未就绪，个别服务会拉取失败，而该 worker 之后只刷新「已知服务」，
#   于是对应上游一直是空节点：/swagger/*.json 返回 503，error.log 里是
#   "failed to set upstream: no valid upstream node: nil"。
#   restart 时网络已就绪，实测能稳定拿到全部四个服务，所以这里创建后自检，不可达就重启重建发现缓存。
#
# 前置：无；服务尚未注册时由本脚本在等待窗口内反复重启网关，服务注册完成后自动收敛
# 用法：./scripts/gateway-dev.sh（run.sh 的 gateway 窗口调用）

set -u

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATEWAY_PORT="${GATEWAY_PORT:-8080}"
SERVICES="spring gozero nestjs fastapi"
# 等待窗口覆盖最慢服务的冷启动耗时，窗口内每 POLL_INTERVAL 秒探测一次、每 RESTART_INTERVAL 秒重建一次
WAIT_SECONDS="${GATEWAY_WAIT_SECONDS:-180}"
POLL_INTERVAL=6
RESTART_INTERVAL=15

cd "$WORKDIR/gateway" || exit 1

# 各服务在 dev 模式下的宿主机端口，与容器编排里的健康检查保持一致
service_port() {
    case $1 in
        spring) echo 8081 ;;
        gozero) echo 8082 ;;
        nestjs) echo 8083 ;;
        fastapi) echo 8084 ;;
    esac
}

# 四个服务未就绪时先不启动网关，避免 forward-auth 在上游不可用时持续刷 connection refused
wait_services() {
    local deadline=$((SECONDS + WAIT_SECONDS)) pending service port

    if ! command -v curl >/dev/null 2>&1; then
        return 0
    fi

    while [ $SECONDS -lt $deadline ]; do
        pending=""
        for service in $SERVICES; do
            port="$(service_port "$service")"
            if ! curl -sf --noproxy '*' -o /dev/null --max-time 3 "http://127.0.0.1:$port/test/$service" 2>/dev/null; then
                pending="$pending $service"
            fi
        done
        if [ -z "$pending" ]; then
            echo "[gateway] 四个服务均已就绪，开始启动网关"
            return 0
        fi
        echo "[gateway] 等待服务就绪:$pending"
        sleep $POLL_INTERVAL
    done

    echo "[gateway] 等待超时，仍有服务未就绪，先启动网关并在窗口内重试"
    return 1
}

check_upstreams() {
    local service code failed=0

    if ! command -v curl >/dev/null 2>&1; then
        return 0
    fi

    for service in $SERVICES; do
        code="$(curl -s --noproxy '*' -o /dev/null -w '%{http_code}' --max-time 5 \
            "http://127.0.0.1:$GATEWAY_PORT/swagger/$service.json" 2>/dev/null)"
        if [ "$code" != "200" ]; then
            echo "[gateway] 上游未就绪: $service（HTTP $code）"
            failed=1
        fi
    done

    return $failed
}

wait_services || true
docker compose up -d

deadline=$((SECONDS + WAIT_SECONDS))
last_restart=$SECONDS
attempt=0
ready=0
while [ $SECONDS -lt $deadline ]; do
    sleep $POLL_INTERVAL
    if check_upstreams; then
        echo "[gateway] 四个服务的 Swagger 规范均可访问"
        ready=1
        break
    fi
    if [ $((SECONDS - last_restart)) -ge $RESTART_INTERVAL ]; then
        attempt=$((attempt + 1))
        echo "[gateway] 重建服务发现缓存（第 $attempt 次 restart）"
        docker compose restart >/dev/null 2>&1 || true
        last_restart=$SECONDS
    fi
done

# 窗口结束时再确认一次，避免恰好在截止前恢复却仍打告警
if [ $ready -ne 1 ] && check_upstreams; then
    echo "[gateway] 四个服务的 Swagger 规范均可访问"
    ready=1
fi

if [ $ready -ne 1 ]; then
    echo "[gateway] 警告：仍有上游不可达，服务就绪后执行 cd gateway && docker compose restart"
fi

# 交回前台跟随日志，Ctrl+C 仍是 compose 默认的停止行为
exec docker compose up
