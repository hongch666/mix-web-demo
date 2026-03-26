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
# package.json 和 package-lock.json 当前不同步，使用 npm install 保持构建可用
RUN npm install --prefer-offline --no-audit

# 复制源代码
COPY src ./src

# 构建应用
RUN npm run node:build

# 阶段2：运行阶段
FROM node:20-alpine

WORKDIR /app

# 安装基础工具
RUN apk add --no-cache curl ca-certificates

# 复制package文件
COPY package*.json ./

# 只安装生产依赖
RUN npm install --omit=dev --prefer-offline --no-audit

# 从构建阶段复制构建产物
COPY --from=builder /app/dist ./dist

# 创建日志目录
RUN mkdir -p /app/logs/nestjs && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload

# 暴露端口（默认8083）
EXPOSE 8083

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:8082/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})" || exit 1

# 启动命令
CMD ["node", "dist/main"]
