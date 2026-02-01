# Spring Boot 应用 Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 阶段1：构建阶段
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /app

# 复制pom.xml
COPY pom.xml .

# 下载依赖（这一步会被缓存）
RUN mvn dependency:go-offline -B

# 复制源代码
COPY src ./src

# 构建应用
RUN mvn clean package -DskipTests -q

# 阶段2：运行阶段
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# 安装基础工具和字体
RUN apk add --no-cache curl ca-certificates && \
    apk add --no-cache font-noto-cjk

# 从构建阶段复制JAR文件
COPY --from=builder /app/target/spring-0.0.1-SNAPSHOT.jar app.jar

# 创建日志目录
RUN mkdir -p /app/logs/spring && \
    mkdir -p /app/static/pic && \
    mkdir -p /app/static/excel && \
    mkdir -p /app/static/upload

# 暴露端口（默认8081）
EXPOSE 8081

# 设置环境变量
ENV JAVA_OPTS="-Xms512m -Xmx1024m -XX:+UseG1GC"

# 启动命令
CMD ["java", "${JAVA_OPTS}", "-jar", "app.jar"]
