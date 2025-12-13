# NestJS 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

# 复制package文件
COPY package*.json ./
COPY tsconfig*.json ./
COPY nest-cli.json ./

# 安装依赖
RUN npm ci --prefer-offline --no-audit

# 复制源代码
COPY src ./src

# 构建应用
RUN npm run build

# 阶段2：运行阶段
FROM node:20-alpine

WORKDIR /app

# 安装基础工具和字体
RUN apk add --no-cache curl ca-certificates && \
    apk add --no-cache font-noto-cjk

# 复制package文件
COPY package*.json ./

# 只安装生产依赖
RUN npm ci --only=production --prefer-offline --no-audit

# 从构建阶段复制构建产物
COPY --from=builder /app/dist ./dist

# 创建日志目录
RUN mkdir -p /app/logs/nestjs && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload

# 暴露端口（默认8082）
EXPOSE 8082

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:8082/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# 启动命令
CMD ["node", "dist/main"]
