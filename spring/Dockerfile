# Spring Boot 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /app

# 复制构建描述与源代码，dependency:go-offline 会额外下载大量插件依赖，
# 直接打包并复用 Maven 缓存可缩短首次镜像构建时间
COPY pom.xml .
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn clean package -DskipTests -q

# 阶段2：运行阶段
FROM eclipse-temurin:17-jre-alpine

ARG OTEL_JAVA_AGENT_VERSION=2.31.1

WORKDIR /app

# 安装基础工具
RUN apk add --no-cache curl ca-certificates

RUN curl -fsSL \
    "https://maven.aliyun.com/repository/public/io/opentelemetry/javaagent/opentelemetry-javaagent/${OTEL_JAVA_AGENT_VERSION}/opentelemetry-javaagent-${OTEL_JAVA_AGENT_VERSION}.jar" \
    -o /app/opentelemetry-javaagent.jar

# 从构建阶段复制JAR文件
# 兼容不同版本名，避免固定版本号导致构建失败
COPY --from=builder /app/target/spring-1.0.0.jar app.jar

# 创建日志目录
RUN mkdir -p /app/logs/spring && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload

# 暴露端口（默认8081）
EXPOSE 8081

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8081/test/spring >/dev/null || exit 1

# 设置环境变量
ENV JAVA_OPTS="-Xms512m -Xmx1024m -XX:+UseG1GC"

# 启动命令
CMD ["sh", "-c", "if [ \"$OTEL_ENABLED\" = \"true\" ]; then OTEL_AGENT_OPTS=-javaagent:/app/opentelemetry-javaagent.jar; fi; exec java $OTEL_AGENT_OPTS $JAVA_OPTS -jar app.jar"]
