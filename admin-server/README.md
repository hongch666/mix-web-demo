## 启动说明

1. 先启动 admin-server 服务，再启动 spring 服务，且使用 Maven 启动
2. 需要查看的参数

| 参数                                                                                                                                 | 说明                                    |
| ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- |
| `hikaricp.connections.active`                                                                                                      | **活跃连接数** （正在被使用）     |
| `hikaricp.connections.idle`                                                                                                        | **空闲连接数** （已建立但未使用） |
| `hikaricp.connections`                                                                                                             | **当前总连接数**                  |
| [hikaricp.connections.max](vscode-file://vscode-app/usr/share/code/resources/app/out/vs/code/electron-browser/workbench/workbench.html) | **最大连接数** （你配置的 20）    |

3. 连接池占用公式

```
占用率(%) = hikaricp.connections.active / hikaricp.connections.max × 100
```

4. `.env`修改后的参数

```.env
# Spring 服务配置
SERVER_ADDRESS=0.0.0.0
SERVER_PORT=8081

# Tomcat 配置
TOMCAT_THREADS_MAX=25
TOMCAT_ACCEPT_COUNT=25
TOMCAT_MAX_CONNECTIONS=100

# MySQL 配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=demo
DB_USERNAME=root
DB_PASSWORD=csc20040312

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DATABASE=0
# REDIS_USERNAME=
# REDIS_PASSWORD=
REDIS_POOL_MAX_ACTIVE=10
REDIS_POOL_MAX_IDLE=5
REDIS_POOL_MIN_IDLE=1
REDIS_TIMEOUT=3000

# RabbitMQ 配置
RABBITMQ_HOST=127.0.0.1
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=hcsy
RABBITMQ_PASSWORD=123456
RABBITMQ_VHOST=test

# 邮件配置
MAIL_HOST=smtp.qq.com
MAIL_PORT=465
MAIL_USERNAME=3070872194@qq.com
MAIL_PASSWORD=skuwsqoctrrwdfgd

# 日志配置
LOGGING_PATH=../logs/spring

# JWT 配置
JWT_SECRET=hcsyhcsyhcsyhcsyhcsycsccsccsccsc
JWT_EXPIRATION=86400000

# Nacos 配置
NACOS_SERVER=127.0.0.1:8848
# Admin Server 配置
ADMIN_SERVER_URL=http://localhost:9095
SERVICE_BASE_URL=http://localhost:8081
```
