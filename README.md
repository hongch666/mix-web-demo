# 多语言技术栈系统

![Java](https://img.shields.io/badge/Java-17+-red?logo=java&logoColor=white)
![Spring](https://img.shields.io/badge/Spring-Boot-6DB33F?logo=spring&logoColor=white)
![Go](https://img.shields.io/badge/Go-1.23+-00ADD8?logo=go&logoColor=white)
![Gin](https://img.shields.io/badge/Gin-Framework-00ADD8?logo=go&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-20+-339933?logo=node.js&logoColor=white)
![NestJS](https://img.shields.io/badge/NestJS-Framework-E0234E?logo=nestjs&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi&logoColor=white)

## 描述

这是一个基于多语言技术栈构建的文章博客管理系统，包含以下组件：

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
5. 基于 RAG 技术，支持 **豆包/Gemini/通义千问** 进行多模型选择的 AI 聊天助手
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
- PostgreSQL：RAG 向量数据库
- MongoDB：非关系型数据库
- Elasticsearch：搜索引擎
- Redis：缓存服务
- RabbitMQ：消息队列
- Hadoop+Hive：大数据存储与分析
- WebSocket：用户实时聊天
- Langchain：大模型调用和 RAG 框架

## 第三方服务

- [火山引擎](https://www.volcengine.com/)
- [Google AI](https://aistudio.google.com/)
- [阿里云百炼平台](https://bailian.console.aliyun.com/)
- [阿里云 OSS](https://oss.console.aliyun.com/overview)

## 环境要求

- Python 3.12+
- Go 1.23+
- Java 17+
- Maven 3.6+
- Node.js 20+
- MySQL 8.0+
- PostgreSQL(需要安装向量插件) 15.4+
- MongoDB 5.0+
- Redis 6.0+
- RabbitMQ 3.8+
- Hadoop+Hive(可选)

## 环境配置脚本

为了简化项目初始化过程，我们提供了自动化配置脚本 `scripts/setup.sh`，可以自动检测环境、安装依赖并配置所有模块。

### Linux/macOS 使用方式

```bash
# 1. 使用便捷脚本调用（推荐）
./services.sh setup

# 或直接调用
./scripts/setup.sh
```

### 交互式配置

运行脚本后会出现以下交互界面：

```bash
# 根据提示选择要配置的模块
# 选项:
# 1) Spring      - 配置 Spring Boot 服务
# 2) Gin         - 配置 Gin 服务
# 3) NestJS      - 配置 NestJS 服务
# 4) FastAPI     - 配置 FastAPI 服务
# 5) 全部        - 配置所有模块
```

### 脚本功能特性

1. **环境检查**

   - 自动检测 Python、Go、Java、Node.js 等必要工具的安装状态和版本
   - 如果缺少必要工具会给出明确提示

2. **系统依赖管理**（仅 FastAPI 模块需要）

   - 自动检测并安装 PostgreSQL 开发库（`libpq-dev`）
   - 自动安装编译工具（`build-essential`、`python3-dev`）
   - 支持多种 Linux 发行版（Ubuntu/Debian、CentOS/RHEL、Fedora、Arch）

3. **模块化安装**

   - 支持选择性安装特定模块或全部安装
   - 每个模块独立配置，互不影响

4. **智能判断**

   - Spring: 自动检测是否有全局 Maven，如果没有则使用 mvnw
   - Gin: 可选安装 fresh（热重载工具）和 swag（Swagger 文档生成工具）
   - FastAPI: 自动安装 uv 并自动创建 uv 虚拟环境并使用阿里镜像源加速安装

5. **目录自动创建**

   - 自动创建 logs 目录（spring、gin、nestjs、fastapi）
   - 自动创建 static 目录（pic、excel、word）

### 脚本执行流程

```bash
./services.sh setup
```

执行后将按以下流程进行：

1. **检测操作系统** - 识别当前 Linux 发行版
2. **检查环境** - 验证必要工具（Python、Go、Java、Node.js、npm）
3. **创建目录** - 自动创建日志和静态文件目录
4. **选择模块** - 交互式选择要配置的模块
5. **安装依赖** - 根据选择自动安装各模块依赖
6. **完成提示** - 显示后续配置步骤

### 注意事项

- **首次运行**: 建议首次配置时选择"全部"选项，确保所有依赖都正确安装
- **系统权限**: 安装系统依赖时可能需要 sudo 权限
- **网络要求**:
  - Go 模块需要访问 GitHub 和 Go 代理
  - Python 使用 uv 配置项目环境，使用阿里镜像源，国内访问速度较快
  - npm 使用默认源，建议配置国内镜像（如淘宝镜像）
- **虚拟环境**: FastAPI 会使用 uv 自动创建虚拟环境（venv），无需手动创建

### 配置完成后

脚本执行完成后，还需要：

1. **配置各服务的 yaml 文件**（见下方"配置文件说明"章节）
2. **启动基础服务**（MySQL、Redis、MongoDB、Elasticsearch、RabbitMQ、Nacos）
3. **使用运行脚本启动服务**（见"运行脚本配置"章节）

## Docker 容器管理

项目提供了 Docker 容器管理脚本，用于快速创建和管理所有依赖的容器服务。

### Docker 容器脚本用法

```bash
# 创建所有容器
./services.sh docker up

# 查看容器状态
./services.sh docker status

# 查看容器日志
./services.sh docker logs <service>

# 停止所有容器
./services.sh docker stop

# 删除所有容器
./services.sh docker delete

# 显示帮助信息
./services.sh docker help
```

### 创建的容器服务

脚本会自动创建以下 Docker 容器：

| 服务              | 端口  | 用户名   | 密码   | 说明                     |
| ----------------- | ----- | -------- | ------ | ------------------------ |
| **MySQL**         | 3306  | root     | 123    | 关系型数据库             |
| **PostgreSQL**    | 5432  | postgres | 123456 | 向量数据库(含 pgvector)  |
| **Redis**         | 6379  | -        | -      | 缓存服务                 |
| **MongoDB**       | 27017 | root     | 123456 | 非关系型数据库           |
| **Elasticsearch** | 9200  | -        | -      | 搜索引擎(7.12.1)         |
| **Nacos**         | 8848  | -        | -      | 服务发现与配置中心       |
| **RabbitMQ**      | 5672  | itheima  | 123321 | 消息队列(管理界面 15672) |

### 脚本功能特性

1. **智能检测**

   - 自动检测 Docker 是否安装和运行
   - 检测端口是否被占用，避免重复创建容器
   - 自动创建项目专用网络 `hcsy`

2. **前置准备**

   - 自动创建数据持久化目录
   - 支持 Elasticsearch IK 分词器安装（可选）
   - 自动生成 Nacos 配置文件

3. **容器管理**

   - 支持查看容器状态
   - 支持查看容器日志
   - 支持停止和删除容器

4. **一键部署**

   - 完整的部署流程自动化
   - 清晰的步骤提示和日志输出

### 快速开始示例

```bash
# 第一次使用：创建所有容器
./services.sh docker up

# 查看所有容器是否正常运行
./services.sh docker status

# 查看 MySQL 容器的日志
./services.sh docker logs mysql

# 需要时停止容器
./services.sh docker stop

# 需要时删除容器
./services.sh docker delete
```

### 注意事项

- **首次创建**: 首次执行 `docker up` 时会创建 Docker 网络，可能需要一些时间
- **数据持久化**: 所有容器的数据都会持久化到宿主机目录
- **Elasticsearch**: 首次创建后会提示是否安装 IK 分词器（可选）
- **Nacos**: 自动生成 `nacos/custom.env` 配置文件，可根据需要修改
- **权限问题**: 如果遇到权限错误，可能需要使用 `sudo` 或将用户加入 docker 组
- 如果有额外创建的组件，按照个人的配置改动配置文件

## 环境设置

> **提示**: 推荐使用上面的 `setup.sh` 配置脚本自动完成以下所有安装步骤。
>
> 如果需要手动配置，可以按照下面的步骤逐个模块进行。

### Spring 部分

使用 Maven 构建：

```bash
cd spring # 进入文件夹
cd gateway # 进入网关
mvn clean install # 下载依赖
./mvnw clean install # Linux/macOS(无全局maven)
mvnw.cmd clean install # Windows(无全局maven)
```

### Gin 部分

```bash
cd gin # 进入文件夹
go mod tidy # 安装依赖
go install github.com/gravityblast/fresh@latest # 修改热启动工具(推荐)
```

### NestJS 部分

```bash
cd nestjs # 进入文件夹
npm install # 安装npm包
bun install # 或者使用bun安装
```

### FastAPI 部分

使用 uv 进行项目管理：

```bash
cd fastapi

# 安装 uv（如果未安装）
# 参考: https://docs.astral.sh/uv/getting-started/installation/

# 配置 uv 虚拟环境
uv venv --python /usr/bin/python3.11 # 创建虚拟环境时指定 Python

# 激活虚拟环境
source .venv/bin/activate

# 同步依赖（使用国内镜像）
uv sync

# 运行项目
uv run python main.py
```

> 项目使用 uv 进行依赖管理，配置文件为 `pyproject.toml`。镜像源配置在 `~/.config/uv/uv.toml`，内容如下

```toml
[[index]]
name = "aliyun"
url = "https://mirrors.aliyun.com/pypi/simple"
default = true

```

## 生产环境部署

本项目提供了统一的打包和部署脚本，可以一键打包所有微服务并统一管理。

**快速打包和部署（方法一：使用便捷脚本）：**

```bash
# 1. 一键打包所有服务
./services.sh build

# 2. 启动所有服务
./services.sh start

# 3. 查看服务状态
./services.sh status

# 4. 重启所有服务（代码更新后）
./services.sh restart

# 5. 停止所有服务
./services.sh stop-dist
```

**快速打包和部署（方法二：直接调用脚本）：**

```bash
# 1. 一键打包所有服务
./scripts/build.sh

# 2. 启动所有服务
./scripts/dist-control.sh start

# 3. 查看服务状态
./scripts/dist-control.sh status

# 4. 重启所有服务
./scripts/dist-control.sh restart

# 5. 停止所有服务
./scripts/dist-control.sh stop
```

打包后的文件统一位于 `dist/` 目录，每个服务都包含配置文件、启动/停止脚本和日志文件。

### 脚本说明

- **services.sh**（项目根目录）

  - 便捷启动器，用于快速调用 `scripts/` 下的脚本
  - 支持开发环境和生产环境命令

- **scripts/build.sh**

  - 编译所有服务：Spring、Gateway、FastAPI、Gin、NestJS
  - 将编译结果打包到 `dist/` 目录
  - 包含编译错误检查和日志输出

- **scripts/dist-control.sh**

  - 管理打包后的分布式服务
  - 支持的操作：`start`、`stop`、`status`、`restart`、`logs`

**示例用法：**

```bash
# 第一次部署
./services.sh build
./services.sh start

# 查看运行状态
./services.sh status

# 代码更新后重新部署
./services.sh build
./services.sh restart

# 停止所有服务
./services.sh stop-dist
```

## 编译和运行项目

> 每个服务都可以独立运行：

### Spring 服务（包括 gateway 网关）

```bash
# 运行Spring服务
cd spring
mvn clean install # 构建项目
mvn spring-boot:run # 启动项目
./mvnw spring-boot:run # Linux/macOS 启动项目(无全局maven)
mvnw.cmd spring-boot:run # Windows 启动项目(无全局maven)
```

### Gin 服务

```bash
# 运行Gin服务
cd gin
go build -o bin/gin main.go # 构建项目
go run main.go # 运行项目(无修改自启插件)
fresh -c ~/.freshrc # 运行项目(有修改自启插件)
```

### NestJS 服务

```bash
# 运行NestJS服务
cd nestjs
npm run start # development
npm run start:dev # watch mode
npm run start:prod # production mode
npm run start:bun:start # bun运行
npm run start:bun:dev # bun运行(watch)
```

### FastAPI 服务

```bash
# 运行FastAPI服务
cd fastapi
uv run python main.py

# 或指定 Python 版本
uv run --python 3.12 python main.py
```

## 运行脚本配置

所有运行脚本已组织到 `scripts/` 目录中，便于项目管理和维护。

### 快速启动（推荐）

#### Linux/macOS

```bash
# 查看帮助信息
./services.sh help

# ===== 开发环境 =====
# 使用多窗格 tmux 布局启动所有服务（推荐用于开发调试）
./services.sh multi

# 使用顺序窗口模式启动所有服务
./services.sh seq

# 停止所有 tmux 服务
./services.sh stop

# ===== 生产环境 =====
# 构建所有服务到 dist/ 目录
./services.sh build

# 启动所有已构建的服务（后台运行）
./services.sh start

# 启动指定的服务
./services.sh start spring gateway
./services.sh start fastapi gin

# 查看已构建服务的运行状态
./services.sh status

# 查看指定服务的运行状态
./services.sh status spring gin

# 重启所有已构建的服务
./services.sh restart

# 重启指定的服务
./services.sh restart fastapi
./services.sh restart spring gateway nestjs

# 停止所有已构建的服务
./services.sh stop-dist

# 停止指定的服务
./services.sh stop-dist spring fastapi

# 查看服务的最新日志（只支持查看单个服务）
./services.sh logs spring
./services.sh logs fastapi
./services.sh logs gin
```

#### Windows

```powershell
# 启动所有服务（PowerShell）
PowerShell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

### 直接调用脚本

如果需要直接调用 `scripts/` 目录下的脚本：

#### Linux/macOS

```bash
# 启动服务（多窗格布局）
./scripts/run_multi.sh

# 启动服务（顺序窗口布局）
./scripts/run.sh

# 停止所有服务
./scripts/stop.sh

# 构建所有服务
./scripts/build.sh

# 管理分布式部署的服务

# 启动所有服务或指定服务
./scripts/dist-control.sh start              # 启动所有
./scripts/dist-control.sh start spring gin   # 启动指定

# 停止所有服务或指定服务
./scripts/dist-control.sh stop               # 停止所有
./scripts/dist-control.sh stop fastapi       # 停止指定

# 查看所有服务状态或指定服务状态
./scripts/dist-control.sh status             # 查看所有
./scripts/dist-control.sh status spring      # 查看指定

# 重启所有服务或指定服务
./scripts/dist-control.sh restart            # 重启所有
./scripts/dist-control.sh restart nestjs     # 重启指定

# 查看单个服务的最新日志
./scripts/dist-control.sh logs spring
./scripts/dist-control.sh logs fastapi
```

#### Windows

```powershell
# 启动所有服务
.\scripts\run.ps1
```

### 脚本说明

| 脚本              | 位置       | 功能                                       | 适用系统    |
| ----------------- | ---------- | ------------------------------------------ | ----------- |
| `services.sh`     | 项目根目录 | 便捷启动器，用于快速调用 scripts/ 下的脚本 | Linux/macOS |
| `run_multi.sh`    | scripts/   | 使用 tmux 多窗格布局启动所有服务（推荐）   | Linux/macOS |
| `run.sh`          | scripts/   | 使用 tmux 顺序窗口模式启动所有服务         | Linux/macOS |
| `stop.sh`         | scripts/   | 停止所有 tmux 服务                         | Linux/macOS |
| `build.sh`        | scripts/   | 编译所有服务到 dist/ 目录                  | Linux/macOS |
| `dist-control.sh` | scripts/   | 管理打包后的分布式服务（支持服务指定）     | Linux/macOS |
| `setup.sh`        | scripts/   | 环境初始化和依赖安装                       | Linux/macOS |
| `ssh.sh`          | scripts/   | SSH 远程端口转发配置                       | Linux/macOS |
| `run.ps1`         | scripts/   | PowerShell 脚本，启动所有服务              | Windows     |

### 服务名称

dist-control.sh 和 services.sh 支持以下服务名称：

- `spring` - Spring Boot 服务
- `gateway` - Spring Cloud Gateway 网关服务
- `fastapi` - FastAPI 服务
- `gin` - Gin 服务
- `nestjs` - NestJS 服务

如不指定服务名称，则对所有服务进行操作。

### 注意事项

1. **tmux 依赖**：Linux/macOS 脚本依赖 `tmux`，请确保已安装
2. **执行权限**：Linux/macOS 脚本需要执行权限，可以通过 `chmod +x scripts/*.sh` 来设置
3. **相对路径**：所有脚本都使用相对路径，可以在任何目录下调用项目的脚本
4. **服务依赖**：启动前请确保 MySQL、Redis、MongoDB、Elasticsearch、RabbitMQ、Nacos 等基础服务已运行
5. **logs 命令**：仅支持查看单个服务的日志，如需查看多个服务请依次调用

## 基础服务组件初始化

### 确保已安装并启动以下数据库服务：

- MySQL
- PostgreSQL
  - 需要安装 `pgvector`插件
- MongoDB
- Redis
- Elasticsearch
- RabbitMQ
- Nacos

### MySQL 表创建(可选，代码会自动创建)

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
    content TEXT COMMENT '评论内容',
    star DOUBLE COMMENT '星级评分，1~10',
    user_id int NOT NULL COMMENT '用户 ID',
    article_id int NOT NULL COMMENT '文章 ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time'
) COMMENT '';
```

- 创建 AI 聊天历史记录

```sql
CREATE TABLE `ai_history` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `ask` TEXT NOT NULL,
    `reply` TEXT NOT NULL,
    `thinking` TEXT,
    `ai_type` VARCHAR(30),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
);
```

### PostgreSQL 表创建

LangChain 会自动创建，但是需要启用 pgvector 扩展

```pgsql
-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;
```

### MongoDB 表创建

- 数据库为 `demo`，集合为 `articlelogs`和 `apilogs`，系统会自动创建

### ElasticSearch 索引创建

- 无需创建，系统同步数据时会自动创建

### Hadoop+Hive 创建

- 无需创建，系统同步数据时会自动创建

## 配置文件说明

### Spring 部分

1. `spring/src/main/resource`目录下有 yaml 配置文件，可以在其中配置对应信息
2. 需要 `application.yaml`和 `bootstrap.yaml`两个配置文件
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
  mail:
    host: smtp.qq.com
    port: 465
    username: xxx@qq.com
    password: xxx # 这个是QQ邮箱的授权码
    properties:
      mail:
        smtp:
          auth: true
          ssl:
            enable: true
logging:
  file:
    path: "../logs/spring"
jwt:
  secret: hcsyhcsyhcsyhcsyhcsyhcsyhcsyhcsy # 至少 32 字节
  expiration: 86400000 # 毫秒数（1 天）
```

- `bootstrap.yaml`

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
  mapper-locations: classpath:mapper/*.xml # 指定 Mapper XML 文件位置
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
  cacheDir: "../static/tmp/nacos/cache"
  logDir: "../static/tmp/nacos/log"

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
  mongodb:
    url: "mongodb://localhost:27017"
    database: "demo"

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
  synchronize: false
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
2. secret 的配置文件是存放阿里云 OSS 的 Key 和 Secret，以及火山引擎平台、 Google AI 平台和阿里云百炼平台的 api_key，不要泄露
3. 可以在 yaml 文件配置静态文件路径，建议配置为主目录下的 `static`
4. 内容如下

- `application.yaml`

```yaml
server:
  ip: 127.0.0.1
  port: 8084
  reload: True
nacos:
  server_addresses: "127.0.0.1:8848"
  namespace: "public"
  service_name: "fastapi"
  group_name: "DEFAULT_GROUP"
rabbitmq:
  host: "127.0.0.1"
  port: 5672
  username: "hcsy"
  password: "123456"
  vhost: "test"
database:
  mysql:
    host: "localhost"
    port: 3306
    database: "demo"
    user: "root"
    password: "csc20040312"
  postgres:
    host: "localhost"
    port: 5432
    database: "demo"
    user: "postgres"
    password: "123456"
    pool_pre_ping: True
    pool_size: 10
    max_overflow: 20
    echo: False
  mongodb:
    url: "mongodb://localhost:27017"
    database: "demo"
  hive:
    host: "127.0.0.1"
    port: 10000
    database: "default"
    table: "articles"
    container: "hive-server"
  redis:
    host: "127.0.0.1"
    port: 6379
    db: 6
    password: ""
    decode_responses: True
    max_connections: 10
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
  upload_path: "../static/upload"
logs:
  path: "../logs/fastapi"
gemini:
  model_name: "gemini-2.0-flash" # 可选: gemini-2.0-pro 等
  timeout: 30 # 请求超时时间（秒）
qwen:
  model_name: "qwen-flash" # 可选: qwen-plus, qwen-turbo, qwen-max 等
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  timeout: 30 # 请求超时时间（秒）
doubao:
  model: "doubao-1-5-lite-32k-250115" # 豆包模型名称
  base_url: "https://ark.cn-beijing.volces.com/api/v3" # 豆包API地址
  timeout: 60 # 请求超时时间（秒）
embedding:
  embedding_model: "text-embedding-v3" # 通义千问嵌入模型（可选: text-embedding-v2, text-embedding-v1）
  top_k: 5 # RAG检索返回的文档数量
  dimension: 1536 # 嵌入维度（text-embedding-v3默认1536维）
  similarity_threshold: 0.3 # 相似度阈值（0-1之间，0.3表示30%相似度及以上才召回）
```

- `application-secret.yaml`

```yaml
oss:
  access_key_id: your_access_key_id
  access_key_secret: your_access_key_secret
gemini:
  api_key: your_api_key
qwen:
  api_key: your_api_key
doubao:
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
            - Path=/articles/list,/api_gin/syncer,/api_fastapi/task/**,/logs,/analyze/excel,/users/batch/{ids}
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
            - Path=/api_gin/**,/search/**, /user-chat/**, /static/**

        - id: nestjs
          uri: lb://nestjs
          predicates:
            - Path=/api_nestjs/**,/logs/**,/download/**,/api-logs/**

        - id: fastapi
          uri: lb://fastapi
          predicates:
            - Path=/api_fastapi/**,/analyze/**,/generate/**,/chat/**,/upload/**,/ai_history/**,/ai_comment/**
jwt:
  secret: hcsyhcsyhcsyhcsyhcsyhcsyhcsyhcsy # 至少 32 字节
  expiration: 2592000000 # 毫秒数（30 天）
```

## Swagger 说明

> 启动时会显示对应的 swagger 地址

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
   @router.get(
       "/fastapi",
       summary="这是接口简介",
       description="这是接口描述"
   )
   def hello():
       """
       这是接口的详细说明
       """
       return {"msg": "hello"}
   ```

3. 启动 FastAPI 服务后，访问 `http://[ip和端口]/docs` 查看 Swagger UI，或访问 `http://[ip和端口]/redoc` 查看 ReDoc 文档。

## 项目文件命名说明

1. Spring 项目采用大驼峰命名方式，如 `UserCreateDTO.java`
2. Gin 项目采用蛇形命名方式，如 `user_create_dto.go`
3. NestJS 项目采用点号命名和下划线命名混合使用的方式，如 `user-create.service.ts`
4. FastAPI 项目采用小驼峰命名方式，如 `userCreateDTO.py`

## 其他说明

1. 词云图的字体应进行配置对应字体的路径。
2. 下载文件的模板需要自行提供，路径在 NestJS 部分 yaml 配置文件中配置，使用 `${字段名}`进行模板书写

- 内容示例

```word
${title}

${tags}

${content}
```

3. FastAPI 模块的阿里云 OSS 的密钥应写在 `application-secret.yaml`中，格式如下：

```yaml
oss:
  access_key_id: your_access_key_id
  access_key_secret: your_access_key_secret
```

4. FastAPI 模块的豆包服务、 Gemini 服务和通义千问服务的 api_key 应写在 `application-secret.yaml`中，格式如下：

```yaml
oss:
  access_key_id: your_access_key_id
  access_key_secret: your_access_key_secret
gemini:
  api_key: your_api_key
qwen:
  api_key: your_api_key
doubao:
  api_key: your_api_key
```

5. Gin 部分的用户聊天相关模块的用户 id 都是字符串，包括数据库存储，请求参数和返回参数。
6. 如果没有使用 Hadoop+Hive 作为大数据分析工具，系统默认使用 pyspark 分析同步时产生的 csv 文章数据。
7. Gemini 服务需要运行的终端使用代理，请自行配置。
8. AI 服务目前只有三种，对应数据库 `user`表里面 `role`为 `ai`的用户，并且代码目前写死用户 id 为 1001/1002/1003，有需要可进行更改。
9. Spring 部分的邮箱登录使用 QQ 邮箱配置发送，需单独配置 QQ 邮箱授权码。
10. Gin 服务若使用 `fresh`修改热启动工具，可以在配置对应配置文件用于修改编译结果产生位置，示例如下

```bash
# Fresh 热启动工具配置文件
# 将编译文件输出到系统临时目录，不污染项目目录

root=.
# 输出到系统临时目录 (/tmp) 而不是项目目录
tmp_path=/tmp/fresh-runner
build_name=runner-build
build_path=/tmp/fresh-runner
build_delay=1000
ignore_folder=assets,tmp,vendor,frontend/node_modules,logs,docs
ignore_file=.DS_Store,.gitignore
watch_path=.
watch_ext=.go
verbose=false
```
