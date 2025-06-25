## 描述

这是一个微服务的 Demo 框架，集成了对 Spring/Gin/Nest.js/FastAPI 微服务注册与发现（Nacos），并使用 SpringCloud 的 gateway 网关进行服务路由和登录校验，可在此基础上进行项目扩展。

## 项目技术栈

- Spring
- MyBatisPlus
- Gin
- Gorm
- NestJS
- TypeORM
- FastAPI
- SQLAlchemy
- Mongoose
- MySQL
- Redis
- ElasticSearch
- MongoDB
- RabbitMQ

## 环境要求

- Java 17 及以上版本
- Maven 3.6+ 版本
- Node 20 及以上版本
- Go 1.20 及以上版本
- Python 3.8 及以上

## 项目设置

```bash
# Nest.js部分
$ cd nestjs # 进入文件夹
$ npm install # 安装npm包
# Gin部分
$ cd gin # 进入文件夹
$ go mod tidy # 安装依赖
$ go install github.com/gravityblast/fresh@latest # 修改自启动工具(推荐)
# Spring部分
$ cd spring # 进入文件夹
$ cd gateway # 进入网关
$ mvn clean install # 下载依赖
# FastAPI部分
$ pip install fastapi uvicorn pyyaml nacos-sdk-python requests sqlalchemy pymysql pymongo wordcloud oss2 jieba
```

## 运行脚本配置

1. 使用`run.sh`运行脚本运行
2. Linux 端使用
3. 需安装`tmux`
4. 更换脚本中运行程序对应的路径（如有需要）
5. 使用`stop.sh`停止所有微服务

## 数据库初始化

1. MySQL 表创建

- 在配置文件中指定对应的数据库
- 创建用户表

```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    email VARCHAR(255) UNIQUE COMMENT '邮箱',
    age INT COMMENT '年龄'
) COMMENT='用户表'
```

- 创建文章表

```sql
CREATE TABLE articles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    title VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',
    content TEXT NOT NULL COMMENT '文章内容',
    user_id BIGINT NOT NULL COMMENT '用户id',
    tags VARCHAR(255) NOT NULL COMMENT '文章标签',
    status INT NOT NULL COMMENT '文章状态',
    views INT NOT NULL COMMENT '文章浏览量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT='文章表'
```

2. MongoDB 表创建

- 数据库为`demo`，集合为`articlelogs`

3. ElasticSearch 索引创建

- 无需创建，系统同步数据时会自动创建

## 编译和运行项目

```bash
# Nest.js部分
$ npm run start # development
$ npm run start:dev # watch mode
$ npm run start:prod # production mode
# Gin部分
$ go build -o bin/gin main.go # 构建项目
$ go run main.go # 运行项目(无修改自启插件)
$ fresh # 运行项目(有修改自启插件)
# Spring部分
mvn clean install # 构建项目
mvn spring-boot:run # 启动项目
```

## 运行测试

```bash
# Nest.js部分
$ npm run test # unit tests
$ npm run test:e2e # e2e tests
$ npm run test:cov # test coverage
# Gin部分
go test ./...
# Spring部分
mvn test
```

## 配置文件说明

### Spring 部分

1. `spring/src/main/resource`目录下有 yaml 配置文件，可以在其中配置对应信息
2. gateway 部分的 yaml 配置文件可以配置路由
3. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的`static`

### Gin 部分

1. `gin`目录下有 yaml 配置文件，可以在其中配置对应信息
2. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的`static`

### Nestjs 部分

1. `nestjs`目录下有 yaml 配置文件，可以在其中配置对应信息
2. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的`static`

### FastAPI 部分

1. `fastapi`目录下有 yaml 配置文件，可以在其中配置对应信息（注意：
2. secret 的配置文件是存放阿里云 OSS 的 Key 和 Secret，不要泄露
3. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的`static`

## Swagger 说明

### Spring 部分

1. 在 config 包下的`SwaggerConfig.java`中修改对应 Swagger 信息

2. 使用`@Operation(summary = "spring自己的测试", description = "输出欢迎信息")`设置对应接口

3. 在`http://[ip和端口]/swagger-ui/index.html`访问 Swagger 接口

### Gin 部分

1. 使用`go install github.com/swaggo/swag/cmd/swag@latest`安装 swag 命令

2. 在 controller 层上的路由函数使用如下注释添加 swagger 信息

```go
// @Summary 获取用户列表
// @Description 获取所有用户信息
// @Tags 用户
// @Produce json
// @Success 200 {array} map[string]string
// @Router /users [get]
```

3. 在`http://[ip和端口]/swagger/index.html`访问 Swagger 接口

4. 每次添加新的 swagger 信息时需要在终端输入`swag init`

### NestJS

1. 在`main.ts`中修改对应 Swagger 信息

2. 使用`@ApiOperation({ summary: '获取用户信息', description: '获取用户信息列表' })`设置对应接口

3. 在`http://[ip和端口]/api-docs`访问 Swagger 接口

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

2. 下载文件的模板需要自行提供，路径在 NestJS 部分 yaml 配置文件中配置，使用`${字段名}`进行模板书写

3. FastAPI 模块的阿里云 OSS 的密钥应写在`application-secret.yaml`中，格式如下：

```yaml
oss:
  access_key_id: your_access_key_id
  access_key_secret: your_access_key_secret
```
