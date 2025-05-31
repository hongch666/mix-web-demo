## 描述

这是一个微服务的 Demo 框架，集成了对 Spring/Gin/Nest.js 微服务注册与发现（Nacos），并使用 SpringCloud 的 gateway 网关进行服务路由，同时 Spring 部分使用 MyBatis-Plus 进行数据库操作，Gin 部分使用 Gorm 进行数据库操作，NestJS 使用 TypeORM 进行数据库操作，可在此基础上进行项目扩展

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
