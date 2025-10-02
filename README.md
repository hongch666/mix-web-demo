# 多语言技术栈微服务系统

## 描述

这是一个基于多种技术栈构建的微服务架构系统，包含以下组件：

- FastAPI（Python）
- Gin（Go）
- Spring Boot（Java）
- NestJS（TypeScript）
- 网关组件

所有服务通过统一网关进行访问，实现了服务治理、认证授权等功能。

## 功能说明

1. 文章/博客发布、修改等操作，并且可以进行搜索引擎式搜索，文章的创建和显示都支持 Markdown
2. 文章操作日志的查看和分析
3. 文章分类，用户状态的管理操作
4. 权限校验实现用户端和管理端
5. 支持 Coze 进行 AI 聊天助手
6. 系统数据的相关数据分析
7. 用户实时聊天功能

## 技术栈

- FastAPI：用于构建 Python 后端服务
- Gin：Go 语言 Web 框架
- Spring Boot：Java 后端框架
- NestJS：TypeScript Node.js 框架
- Spring Cloud Gateway：API 网关
- JWT：身份验证
- Nacos：服务发现与配置中心
- MySQL：关系型数据库
- MongoDB：非关系型数据库
- Elasticsearch：搜索引擎
- Redis：缓存服务
- RabbitMQ：消息队列
- Hadoop+Hive：大数据存储与分析
- WebSocket：用户实时聊天

## 第三方服务

- [CozeAI](https://www.coze.cn/home)
- [Gemini API](https://aistudio.google.com/)

## 环境要求

- Python 3.12+
- Go 1.23+
- Java 17+
- Maven 3.6+
- Node.js 20+
- MySQL 8.0+
- MongoDB 5.0+
- Redis 6.0+
- RabbitMQ 3.8+
- Hadoop+Hive(可选)

## 项目设置

### FastAPI 部分

```bash
cd fastapi
python3 -m venv venv
source venv/bin/activate # Linux
venv\Scripts\activate # Windows
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 如需退出虚拟环境，执行 `deactivate`

### Gin 部分

```bash
cd gin # 进入文件夹
go mod tidy # 安装依赖
go install github.com/gravityblast/fresh@latest # 修改自启动工具(推荐)
```

### Spring 部分

使用 Maven 构建：

```bash
cd spring # 进入文件夹
cd gateway # 进入网关
mvn clean install # 下载依赖
./mvnw clean install # Linux/macOS(无全局maven)
mvnw.cmd clean install # Windows(无全局maven)
```

### NestJS 部分

```bash
cd nestjs # 进入文件夹
npm install # 安装npm包
```

## 运行脚本配置

使用提供的运行脚本启动各个服务：

### Linux/macOS

```bash
# 启动所有服务
./run.sh

# 停止所有服务
./stop.sh
```

### Windows

```powershell
.\run.ps1
```

如需关闭服务，请手动关闭对应窗口。

### 注意

如果未全局安装 maven，需修改 Spring 和 Gateway 部分的启动脚本的指令。

## 基础服务组件初始化

1. 确保已安装并启动以下数据库服务：

- MySQL
- MongoDB
- Redis
- Elasticsearch
- RabbitMQ
- Nacos

2. MySQL 表创建(可选，代码会自动创建)

- 在配置文件中指定对应的数据库
- 创建用户表

```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    email VARCHAR(255) UNIQUE COMMENT '邮箱',
    age INT COMMENT '年龄',
    role VARCHAR(255) NOT NULL COMMENT '用户权限',
    img VARCHAR(255) COMMENT '用户头像'
) COMMENT='用户表'
```

- 创建文章表

```sql
CREATE TABLE articles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    title VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',
    content TEXT NOT NULL COMMENT '文章内容',
    user_id BIGINT NOT NULL COMMENT '用户id',
    sub_category_id BIGINT NOT NULL COMMENT '子分类id',
    tags VARCHAR(255) NOT NULL COMMENT '文章标签',
    status INT NOT NULL COMMENT '文章状态',
    views INT NOT NULL COMMENT '文章浏览量',
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT='文章表'
```

- 创建分类表

```sql
CREATE TABLE category (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    name VARCHAR(255) NOT NULL COMMENT '分类名称',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT='分类表';
```

- 创建子分类表

```sql
CREATE TABLE sub_category (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    name VARCHAR(255) NOT NULL COMMENT '子分类名称',
    category_id BIGINT NOT NULL COMMENT '所属分类ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE
) COMMENT='子分类表';
```

- 创建用户聊天历史记录表

```sql
CREATE TABLE `chat_messages` (
    `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '消息ID，主键',
    `sender_id` varchar(50) NOT NULL COMMENT '发送者用户ID',
    `receiver_id` varchar(50) NOT NULL COMMENT '接收者用户ID',
    `content` text NOT NULL COMMENT '消息内容',
    `created_at` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_chat_messages_sender_id` (`sender_id`) COMMENT '发送者ID索引',
    KEY `idx_chat_messages_receiver_id` (`receiver_id`) COMMENT '接收者ID索引',
    KEY `idx_chat_messages_created_at` (`created_at`) COMMENT '创建时间索引',
    KEY `idx_chat_messages_sender_receiver` (
        `sender_id`,
        `receiver_id`,
        `created_at`
    ) COMMENT '发送者接收者组合索引，用于查询聊天历史'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '聊天消息表';
```

- 创建文章评论表

```sql
CREATE TABLE comments (
    id int NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary Key',
    content VARCHAR(255) COMMENT '评论内容',
    star DOUBLE COMMENT '星级评分，1~10',
    user_id int NOT NULL COMMENT '用户 ID',
    article_id int NOT NULL COMMENT '文章 ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time'
) COMMENT '';
```

3. MongoDB 表创建

- 数据库为 `demo`，集合为 `articlelogs`

4. ElasticSearch 索引创建

- 无需创建，系统同步数据时会自动创建

5. Hadoop+Hive 创建

- 无需创建，系统同步数据时会自动创建

## 编译和运行项目

每个服务都可以独立运行：

```bash
# 运行FastAPI服务
cd fastapi
source venv/bin/activate # Linux
venv\Scripts\activate # Windows
python3 -u main.py

# 运行Gin服务
cd gin
go build -o bin/gin main.go # 构建项目
go run main.go # 运行项目(无修改自启插件)
fresh # 运行项目(有修改自启插件)

# 运行Spring服务
cd spring
mvn clean install # 构建项目
mvn spring-boot:run # 启动项目
./mvnw spring-boot:run # Linux/macOS 启动项目(无全局maven)
mvnw.cmd spring-boot:run # Windows 启动项目(无全局maven)

# 运行NestJS服务
cd nestjs
npm run start # development
npm run start:dev # watch mode
npm run start:prod # production mode
```

## 配置文件说明

### Spring 部分

1. `spring/src/main/resource`目录下有 yaml 配置文件，可以在其中配置对应信息
2. gateway 部分的 yaml 配置文件可以配置路由
3. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的 `static`
4. 内容如下

- `application.yaml`

```yaml
server:
  address: 0.0.0.0
  port: 8081
  tomcat:
    threads:
      max: 25
    accept-count: 25
    max-connections: 100
spring:
  application:
    name: spring
  data:
    redis:
      host: localhost
      port: 6379
      database: 0
      lettuce:
        pool:
          max-active: 10
          max-idle: 5
          min-idle: 1
      timeout: 3000
  rabbitmq:
    host: 127.0.0.1
    port: 5672
    username: hcsy
    password: 123456
    virtual-host: test
logging:
  file:
    path: "../logs/spring"
jwt:
  secret: hcsyhcsyhcsyhcsyhcsyhcsyhcsyhcsy # 至少 32 字节
  expiration: 86400000 # 毫秒数（1 天）
```

- `bootstrap.yml`

```yml
spring:
  config:
    import:
      - "nacos:application.yml" # 将 DataId 明确设为 application.yml
      - "optional:nacos:application-dev.yml?group=DEV_GROUP"
  datasource:
    url: jdbc:mysql://localhost:3306/demo?useSSL=false&useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai
    username: root
    password: csc20040312
    driver-class-name: com.mysql.cj.jdbc.Driver
  cloud:
    nacos:
      config:
        server-addr: 127.0.0.1:8848 # Nacos 服务端地址

mybatis-plus:
  configuration:
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl # 打印 SQL（可选）
  global-config:
    db-config:
      id-type: auto # 主键策略
      logic-delete-field: deleted # 逻辑删除字段
```

### Gin 部分

1. `gin`目录下有 yaml 配置文件，可以在其中配置对应信息
2. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的 `static`
3. 内容如下

- `application.yaml`

```yaml
server:
  ip: 127.0.0.1
  port: 8082

nacos:
  ipAddr: 127.0.0.1
  port: 8848
  namespace: "public"
  serviceName: gin
  groupName: DEFAULT_GROUP
  clusterName: DEFAULT

database:
  mysql:
    host: 127.0.0.1
    port: 3306
    username: root
    password: csc20040312
    dbname: demo
    charset: utf8mb4
    loc: Local
  es:
    url: http://127.0.0.1:9200
    sniff: false

mq:
  username: hcsy
  password: 123456
  host: 127.0.0.1
  port: 5672
  vhost: test

logs:
  path: "../logs/gin"
```

### Nestjs 部分

1. `nestjs`目录下有 yaml 配置文件，可以在其中配置对应信息
2. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的 `static`
3. 内容如下

- `application.yaml`

```yaml
server:
  ip: 127.0.0.1
  port: 8083
  serviceName: nestjs
nacos:
  server-addr: 127.0.0.1
  namespace: public
  clusterName: DEFAULT
database:
  type: mysql
  host: localhost
  port: 3306
  username: root
  password: csc20040312
  database: demo
  synchronize: true
  logging: false
  entities:
    - src/**/*.entity.js
mongodb:
  url: mongodb://localhost:27017
  dbName: demo
rabbitmq:
  host: localhost
  port: 5672
  username: hcsy
  password: 123456
  vhost: test
files:
  word: ../static/word
logs:
  path: "../logs/nestjs"
```

### FastAPI 部分

1. `fastapi`目录下有 yaml 配置文件，可以在其中配置对应信息（注意：
2. secret 的配置文件是存放阿里云 OSS 的 Key 和 Secret，以及 COZE 平台和 Gemini 平台的 api_key，不要泄露
3. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的 `static`
4. 内容如下

- `application.yaml`

```yaml
server:
  ip: 127.0.0.1
  port: 8084
nacos:
  server_addresses: "127.0.0.1:8848"
  namespace: "public"
  service_name: "fastapi"
  group_name: "DEFAULT_GROUP"
database:
  mysql:
    url: "mysql+pymysql://root:csc20040312@localhost/demo?charset=utf8mb4"
  mongodb:
    url: "mongodb://localhost:27017"
    database: "demo"
  hive:
    host: "127.0.0.1"
    port: 10000
    database: "default"
    table: "articles"
    container: "hive-server"
oss:
  bucket_name: mix-web-demo
  endpoint: oss-cn-guangzhou.aliyuncs.com
wordcloud:
  font_path: "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
  width: 800
  height: 400
  background_color: "white"
files:
  pic_path: "../static/pic"
  excel_path: "../static/excel"
logs:
  path: "../logs/fastapi"
coze:
  bot_id: "7521289882573324298"
  base_url: "https://api.coze.cn"
  timeout: 30
gemini:
  model_name: "gemini-2.0-flash" # 可选: gemini-1.5-pro, gemini-1.5-flash 等
  timeout: 30 # 请求超时时间（秒）
```

- `application-secret.yaml`

```yaml
oss:
  access_key_id: your_access_key_id
  access_key_secret: your_access_key_secret
coze:
  api_key: your_api_key
gemini:
  api_key: your_api_key
```

### Gateway 部分

1. `gateway/src/main/resource`目录下有 yaml 配置文件，可以在其中配置对应信息
2. gateway 部分的 yaml 配置文件可以配置路由
3. 内容如下

- `application.yaml`

```yaml
server:
  port: 8080
spring:
  application:
    name: gateway
  cloud:
    nacos:
      server-addr: 127.0.0.1:8848
    gateway:
      # 全局WebSocket支持
      globalcors:
        cors-configurations:
          "[/**]":
            allowedOrigins: "*"
            allowedMethods: "*"
            allowedHeaders: "*"
      routes:
        # 1. 先排除特殊路径
        - id: exclude-list
          uri: no://op
          predicates:
            - Path=/articles/list,/api_gin/syncer,/api_fastapi/task,/logs,/analyze/excel,/category/sub/batch/{id},/category/batch/{ids},/users/batch/{ids},/category/all,/category/sub/all
          filters:
            - SetStatus=204

        # 2. 正常路由
        - id: spring
          uri: lb://spring
          predicates:
            - Path=/api_spring/**,/users/**,/articles/**,/category/**,/comments/**

        - id: gin-ws
          uri: ws://localhost:8082
          predicates:
            - Path=/ws/**
          metadata:
            # WebSocket 相关配置
            connect-timeout: 60000
            response-timeout: 60000

        - id: gin
          uri: lb://gin
          predicates:
            - Path=/api_gin/**,/search, /user-chat/**, /static/**

        - id: nestjs
          uri: lb://nestjs
          predicates:
            - Path=/api_nestjs/**,/logs/**,/article/**

        - id: fastapi
          uri: lb://fastapi
          predicates:
            - Path=/api_fastapi/**,/analyze/**,/generate/**,/chat/**,/upload/**
jwt:
  secret: hcsyhcsyhcsyhcsyhcsyhcsyhcsyhcsy # 至少 32 字节
  expiration: 2592000000 # 毫秒数（30 天）
```

## Swagger 说明

### Spring 部分

1. 在 config 包下的 `SwaggerConfig.java`中修改对应 Swagger 信息
2. 使用 `@Operation(summary = "spring自己的测试", description = "输出欢迎信息")`设置对应接口
3. 在 `http://[ip和端口]/swagger-ui/index.html`访问 Swagger 接口

### Gin 部分

1. 使用 `go install github.com/swaggo/swag/cmd/swag@latest`安装 swag 命令
2. 在 controller 层上的路由函数使用如下注释添加 swagger 信息

```go
// @Summary 获取用户列表
// @Description 获取所有用户信息
// @Tags 用户
// @Produce json
// @Success 200 {array} map[string]string
// @Router /users [get]
```

3. 在 `http://[ip和端口]/swagger/index.html`访问 Swagger 接口
4. 每次添加新的 swagger 信息时需要在终端输入 `swag init`

### NestJS

1. 在 `main.ts`中修改对应 Swagger 信息
2. 使用 `@ApiOperation({ summary: '获取用户信息', description: '获取用户信息列表' })`设置对应接口
3. 在 `http://[ip和端口]/api-docs`访问 Swagger 接口

### FastAPI 部分

1. 在 `main.py` 中通过 `FastAPI` 的参数自定义全局 Swagger 信息，例如：

   ```python
   app = FastAPI(
       title="FastAPI部分的Swagger文档集成",
       description="这是demo项目的FastAPI部分的Swagger文档集成",
       version="1.0.0"
   )
   ```

2. 单个接口的描述可以通过路由装饰器的 `description` 参数或函数 docstring 设置，例如：

   ```python
   @router.get("/hello", description="这是一个自定义的接口描述")
   def hello():
       """
       这是接口的详细说明
       """
       return {"msg": "hello"}
   ```

3. 启动 FastAPI 服务后，访问 `http://[ip和端口]/docs` 查看 Swagger UI，或访问 `http://[ip和端口]/redoc` 查看 ReDoc 文档。

## 其他说明

1. 词云图的字体应进行配置对应字体的路径。
2. 下载文件的模板需要自行提供，路径在 NestJS 部分 yaml 配置文件中配置，使用 `${字段名}`进行模板书写
3. FastAPI 模块的阿里云 OSS 的密钥应写在 `application-secret.yaml`中，格式如下：

```yaml
oss:
  access_key_id: your_access_key_id
  access_key_secret: your_access_key_secret
```

4. FastAPI 模块的 COZE 服务和 Gemini 服务 的 api_key 应写在 `application-secret.yaml`中，格式如下：

```yaml
coze:
  api_key: your_api_key
gemini:
  api_key: your_api_key
```

5. Gin 部分的用户聊天相关模块的用户 id 都是字符串，包括数据库存储，请求参数和返回参数。
