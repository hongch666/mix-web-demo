# syntax=docker/dockerfile:1.7
# Go-Zero 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM golang:1.23.5-alpine3.20 AS builder

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
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -a -installsuffix cgo \
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

# 从构建阶段复制应用
COPY --from=builder /app/gozero-app .

# 复制配置文件
COPY app/etc ./etc

# 创建非root用户提高安全性
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# 创建日志和文件目录并设置权限
RUN mkdir -p /app/logs/gozero && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload && \
    chown -R appuser:appgroup /app/logs /app/static && \
    chmod -R 755 /app

USER appuser

# 暴露端口（默认8082）
EXPOSE 8082

# 运行应用
ENTRYPOINT ["./gozero-app", "-f", "etc/application.yaml"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8082/api_gozero/gozero || exit 1
