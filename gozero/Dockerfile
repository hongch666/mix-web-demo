# syntax=docker/dockerfile:1.7
# Go-Zero 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM golang:1.24-alpine3.20 AS builder

WORKDIR /app

# 允许外部覆盖 Go 模块代理，默认使用国内镜像提升下载稳定性
ARG GOPROXY=https://goproxy.cn,direct
ENV GOPROXY=${GOPROXY}

# 安装构建依赖
# 不锁定精确版本，避免 Alpine 仓库更新后构建失败
RUN apk add --no-cache git make

# 使用 --platform 标志支持跨平台构建
# 复制go文件
COPY app/go.mod app/go.sum ./

# 下载依赖
# 使用 BuildKit cache 缓存模块和编译产物，减少重复下载
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download

# 复制源代码
COPY app .

# 构建应用（禁用CGO以避免glibc依赖）
# 与 go mod download 复用同一份 cache mount：cache mount 内容不写入镜像层，
# 不挂载时源码变更会退化为重新下载全部模块
# 同时去掉 -a，让 go build 复用编译缓存而不是每次重编标准库
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -installsuffix cgo \
    -ldflags="-w -s" \
    -o gozero-app .

# 阶段2：运行阶段
# 使用具体的 alpine 版本而不是 latest
FROM alpine:3.20

WORKDIR /app

# 更新基础镜像并安装最少运行时依赖
# 分离 ca-certificates 安装以避免重复
RUN apk update && \
    apk add --no-cache \
    ca-certificates \
    curl \
    tzdata && \
    rm -rf /var/cache/apk/*

# 进程时区固定为东八区，保证日志行时间、cron 调度与业务日期口径一致
ENV TZ=Asia/Shanghai

# 从构建阶段复制应用
COPY --from=builder /app/gozero-app .

# 复制配置文件
COPY app/etc ./etc

# 创建非root用户提高安全性
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# 创建日志、静态文件与 Nacos 缓存/日志目录并设置权限
# Nacos 目录默认在 /app/tmp 下（cacheDir/logDir 相对 ./tmp 解析），非 root 用户需要预建授权
# 容器实际以宿主机 UID 运行（compose 的 HOST_UID 与脚本的 --user），与镜像内 appuser 的 1001 不一致
# 因此 /app/tmp 放开写权限，否则 Nacos SDK 写 nacos-sdk.log 会报 permission denied
RUN mkdir -p /app/logs/gozero && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload && \
    mkdir -p /app/tmp/nacos/cache && \
    mkdir -p /app/tmp/nacos/log && \
    chown -R appuser:appgroup /app/logs /app/static /app/tmp && \
    chmod -R 755 /app/logs /app/static && \
    chmod -R 777 /app/tmp && \
    chmod 755 /app

USER appuser

# 暴露端口（默认8082）
EXPOSE 8082

# 运行应用
ENTRYPOINT ["./gozero-app", "-f", "etc/application.yaml"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8082/test/gozero >/dev/null || exit 1
