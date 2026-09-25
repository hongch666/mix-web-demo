# Spring Boot 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /app

# 复制构建描述、格式化配置与源代码，dependency:go-offline 会额外下载大量插件依赖，
# 直接打包并复用 Maven 缓存可缩短首次镜像构建时间
# eclipse-formatter.xml 为 pom.xml 中 Spotless 校验所需的格式化配置，validate 阶段会读取
COPY pom.xml .
COPY eclipse-formatter.xml .
COPY settings-docker.xml .
COPY src ./src
ARG MAVEN_PROXY_HOST=
ARG MAVEN_PROXY_PORT=
RUN --mount=type=cache,target=/root/.m2 \
    if [ -n "${MAVEN_PROXY_HOST}" ] && [ -n "${MAVEN_PROXY_PORT}" ]; then \
      proxy_active=true; \
    else \
      proxy_active=false; \
    fi; \
    sed -i "s/__MAVEN_PROXY_ACTIVE__/${proxy_active}/; s/__MAVEN_PROXY_HOST__/${MAVEN_PROXY_HOST:-127.0.0.1}/; s/__MAVEN_PROXY_PORT__/${MAVEN_PROXY_PORT:-1}/" settings-docker.xml && \
    mvn -s settings-docker.xml clean package -DskipTests -Dspotless.check.skip=true -q

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
