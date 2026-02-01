# Gin 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM golang:1.23-alpine AS builder

WORKDIR /app

# 安装构建依赖
RUN apk add --no-cache git make

# 复制go文件
COPY go.mod go.sum ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 构建应用
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o gin-app .

# 阶段2：运行阶段
FROM alpine:latest

WORKDIR /app

# 安装运行时依赖和字体
RUN apk add --no-cache ca-certificates curl tzdata && \
    apk add --no-cache font-noto-cjk

# 复制证书
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# 从构建阶段复制应用
COPY --from=builder /app/gin-app .

# 创建日志和文件目录
RUN mkdir -p /app/logs/gin && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload

# 暴露端口（默认8082）
EXPOSE 8082

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8082/api_gin/gin || exit 1

# 启动命令
CMD ["./gin-app"]
