# Go-Zero 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM golang:1.23.0-alpine3.20 AS builder

WORKDIR /app

# 安装构建依赖
RUN apk add --no-cache git=2.43.4-r0 make=4.4.1-r2

# 使用 --platform 标志支持跨平台构建
# 复制go文件
COPY app/go.mod app/go.sum ./

# 下载依赖
RUN go mod download

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

# 创建日志和文件目录
RUN mkdir -p /app/logs && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload && \
    chmod -R 755 /app

# 创建非root用户提高安全性
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

USER appuser

# 暴露端口（默认8082）
EXPOSE 8082

# 运行应用
ENTRYPOINT ["./gozero-app", "-f", "etc/application.yaml"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8082/api_gin/gin || exit 1
