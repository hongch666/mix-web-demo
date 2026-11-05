#!/bin/bash

set -e

# docker-compose 方式启动整套服务
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

# 确保与 docker-services.sh 使用同一网络
if ! docker network inspect hcsy >/dev/null 2>&1; then
    echo "Docker网络 hcsy 不存在，正在创建..."
    docker network create hcsy
fi

# 预创建日志目录，网关日志可能由 APISIX 用户创建，不能递归修改已有文件
for d in gateway spring gozero nestjs fastapi; do
    mkdir -p "$WORKDIR/logs/$d"
    chmod 777 "$WORKDIR/logs/$d" 2>/dev/null || \
        echo "警告：无法修改日志目录权限，将由容器初始化步骤处理: $WORKDIR/logs/$d"
done

# 预创建静态目录
for d in pic excel upload; do
    mkdir -p "$WORKDIR/static/$d"
    chmod -R 777 "$WORKDIR/static/$d"
done

# 远程镜像前缀：未在环境中配置时读取根目录 .env 的 DOCKER_IMAGE_PREFIX
# 取值必须以 / 结尾（例如 docker.io/yourname/），与 docker-compose.yml 的镜像名拼接规则一致
if [ -z "${DOCKER_IMAGE_PREFIX:-}" ] && [ -f "$WORKDIR/.env" ]; then
    # .env 未启用该键时 grep 返回 1，避免在 set -e 下让赋值语句失败退出脚本
    DOCKER_IMAGE_PREFIX="$(grep -E '^DOCKER_IMAGE_PREFIX=' "$WORKDIR/.env" | tail -n 1 | cut -d= -f2-)" || true
fi

app_services=(spring gozero nestjs fastapi)
missing_images=()
retag_images=()

for service in "${app_services[@]}"; do
    effective_image="${DOCKER_IMAGE_PREFIX:-}mix-${service}:latest"
    if docker image inspect "$effective_image" >/dev/null 2>&1; then
        continue
    fi
    # 本地构建镜像存在时补打同名标签，保证本地构建结果优先于远程镜像
    if docker image inspect "mix-${service}:latest" >/dev/null 2>&1; then
        retag_images+=("$service")
        continue
    fi
    missing_images+=("$service")
done

for service in "${retag_images[@]}"; do
    docker tag "mix-${service}:latest" "${DOCKER_IMAGE_PREFIX:-}mix-${service}:latest"
    echo "本地构建镜像已补打标签: ${DOCKER_IMAGE_PREFIX:-}mix-${service}:latest"
done

if [ ${#missing_images[@]} -gt 0 ]; then
    if [ -n "${DOCKER_IMAGE_PREFIX:-}" ]; then
        echo "本地缺少镜像: ${missing_images[*]}，已配置 DOCKER_IMAGE_PREFIX，由 compose 从远程仓库拉取"
    else
        echo "缺少应用镜像，使用 mix Docker 脚本构建: ${missing_images[*]}"
        bash "$WORKDIR/mix" docker build "${missing_images[@]}"
    fi
else
    echo "应用镜像已存在，跳过镜像构建"
fi

# 清理 dev 模式残留的网关容器，根 compose 与 gateway/docker-compose.yml 共用
# container_name: mix-gateway，不清理会因容器名冲突导致本次启动失败
bash "$WORKDIR/scripts/gateway-cleanup.sh"

# 清理 ./mix loki start 独立启动的观测栈容器，观测栈在本编排中
# 内联定义，loki-config/docker-compose.yml 是其独立启动版本，两者容器名相同但属于不同
# compose 项目，独立栈残留会因容器名冲突导致本次启动失败
bash "$WORKDIR/scripts/loki-control.sh" cleanup || true

echo "启动应用与可观测性服务，不含第三方依赖组件"

echo "请先通过 ./scripts/docker-services.sh 启动 MySQL/Redis/MongoDB/ES/Nacos/RabbitMQ/ClickHouse 等依赖"

# 应用镜像此时已就绪，这里只会串行拉取缺失的第三方镜像；
# 规避 docker compose v2.35.x 并发拉取镜像的 fatal error: concurrent map writes（docker/compose#12747）
bash "$WORKDIR/scripts/prepull-images.sh" "$COMPOSE_FILE" "$COMPOSE_CMD"

$COMPOSE_CMD -f "$COMPOSE_FILE" up -d

# 网关的 Nacos 发现按 worker 各自缓存，启动瞬间没拉到实例的服务会一直保持空上游并返回 503，
# 这里复用 dev 模式的收敛逻辑：轮询四个服务的规范，不可达就重启网关重建发现缓存
if command -v curl >/dev/null 2>&1; then
    GATEWAY_WAIT_SECONDS="${GATEWAY_WAIT_SECONDS:-180}"
    GATEWAY_PORT="${GATEWAY_PORT:-8080}"
    gateway_ready=0
    deadline=$((SECONDS + GATEWAY_WAIT_SECONDS))
    last_restart=$SECONDS

    while [ $SECONDS -lt $deadline ]; do
        pending=""
        for service in spring gozero nestjs fastapi; do
            code="$(curl -s --noproxy '*' -o /dev/null -w '%{http_code}' --max-time 5 \
                "http://127.0.0.1:$GATEWAY_PORT/swagger/$service.json" 2>/dev/null || true)"
            [ "$code" = "200" ] || pending="$pending $service"
        done
        if [ -z "$pending" ]; then
            gateway_ready=1
            break
        fi
        echo "网关上游未就绪:$pending"
        if [ $((SECONDS - last_restart)) -ge 15 ]; then
            echo "重启网关重建 Nacos 服务发现缓存"
            $COMPOSE_CMD -f "$COMPOSE_FILE" restart gateway >/dev/null 2>&1 || true
            last_restart=$SECONDS
        fi
        sleep 5
    done

    if [ $gateway_ready -eq 1 ]; then
        echo "四个服务经网关均可访问"
    else
        echo "警告：仍有服务经网关不可达，服务就绪后执行 $COMPOSE_CMD -f $COMPOSE_FILE restart gateway"
    fi
fi

echo "应用服务已启动，使用 $COMPOSE_CMD -f $COMPOSE_FILE ps 查看状态"
