#!/bin/bash

# 脚本说明：dev 模式启动 APISIX 网关
#
# 背景：`docker compose up` 创建容器的瞬间，APISIX 的 Nacos 发现模块会并发拉取各服务实例，
#   此时容器网络可能尚未就绪，个别服务会拉取失败，而该 worker 之后只刷新「已知服务」，
#   于是对应上游一直是空节点：/swagger/*.json 返回 503，error.log 里是
#   "failed to set upstream: no valid upstream node: nil"。
#   restart 时网络已就绪，实测能稳定拿到全部四个服务，所以这里创建后自检，不可达就重启一次。
#
# 前置：四个服务已在 Nacos 注册（run.sh 的 wait_nacos_registration 已保证）
# 用法：./scripts/gateway-dev.sh（run.sh 的 gateway 窗口调用）

set -u

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATEWAY_PORT="${GATEWAY_PORT:-8080}"
SERVICES="spring gozero nestjs fastapi"
MAX_ATTEMPT=3

cd "$WORKDIR/gateway" || exit 1

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

docker compose up -d

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPT" ]; do
    sleep 6
    if check_upstreams; then
        echo "[gateway] 四个服务的 Swagger 规范均可访问"
        break
    fi
    if [ "$attempt" -lt "$MAX_ATTEMPT" ]; then
        echo "[gateway] 重建服务发现缓存（第 $attempt 次 restart）"
        docker compose restart >/dev/null 2>&1 || true
    else
        echo "[gateway] 警告：仍有上游不可达，服务就绪后执行 cd gateway && docker compose restart"
    fi
    attempt=$((attempt + 1))
done

# 交回前台跟随日志，Ctrl+C 仍是 compose 默认的停止行为
exec docker compose up
