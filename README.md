## 描述

这是一个微服务的 Demo 框架，集成了对 Spring/Gin/Nest.js 微服务注册与发现（Nacos），并使用 SpringCloud 的 gateway 网关进行服务路由和登录校验，可在此基础上进行项目扩展。

## 项目技术栈

- Spring
- MyBatisPlus
- Gin
- Gorm
- NestJS
- TypeORM
- Mongoose
- MySQL
- Redis
- ElasticSearch
- MongoDB

## 环境要求

- Java 17 及以上版本
- Maven 3.6+ 版本
- Node 20 及以上版本
- Go 1.20 及以上版本

## 项目设置

```bash
# Nest.js部分
$ cd nestjs # 进入文件夹
$ npm install # 安装npm包
# Gin部分
$ cd gin # 进入文件夹
$ go mod tidy # 安装依赖
# Spring部分
$ cd spring # 进入文件夹
$ cd gateway # 进入网关
$ mvn clean install # 下载依赖
```

## 编译和运行项目

```bash
# Nest.js部分
$ npm run start # development
$ npm run start:dev # watch mode
$ npm run start:prod # production mode
# Gin部分
$ go build -o bin/gin main.go # 构建项目
$ go run main.go # 运行项目
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

1. `spring/src/main/resource`目录下有 yaml 配置文件，可以在其中配置 nacos 地址、微服务名等信息
2. gateway 部分的 yaml 配置文件可以配置路由

### Gin 部分

1. `gin`目录下有 yaml 配置文件，可以在其中配置 nacos 地址、微服务名等信息

### Nestjs 部分

1. `nestjs`目录下有 yaml 配置文件，可以在其中配置 nacos 地址、微服务名等信息

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
