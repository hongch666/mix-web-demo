# syntax=docker/dockerfile:1

# NestJS 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

ENV PUPPETEER_SKIP_DOWNLOAD=true

# 复制package文件
COPY package*.json ./
COPY tsconfig*.json ./
COPY nest-cli.json ./

# 安装构建依赖
RUN --mount=type=cache,target=/root/.npm \
    npm ci --include=dev --prefer-offline --no-audit --no-fund \
    --fetch-retries=5 --fetch-retry-factor=2 \
    --fetch-retry-mintimeout=1000 --fetch-retry-maxtimeout=60000

# 复制源代码
COPY src ./src

# 构建应用
RUN npm run node:build && npm prune --omit=dev --no-audit --no-fund

# 阶段2：运行阶段
FROM node:20-alpine

WORKDIR /app

ENV PUPPETEER_SKIP_DOWNLOAD=true

# 安装基础工具
RUN apk add --no-cache curl ca-certificates

# 复制生产依赖和package文件
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

# 从构建阶段复制构建产物
COPY --from=builder /app/dist ./dist

# 复制默认配置文件（与 src/config/application.yaml 保持同步）
COPY src/config/application.yaml ./dist/config/application.yaml

# 创建日志目录
RUN mkdir -p /app/logs/nestjs && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload && \
    chown -R node:node /app/logs/nestjs /app/static

# 暴露端口（默认8083）
EXPOSE 8083

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8083/test/nestjs >/dev/null || exit 1

# 启动命令
CMD ["node", "dist/main"]
