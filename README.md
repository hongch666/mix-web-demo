# 基于 RAG 知识问答与 LLM 驱动推荐的 IT 智能文章推荐与知识问答系统(多语言技术栈构建)

![Java](https://img.shields.io/badge/Java-17+-red?logo=java&logoColor=white)
![Spring](https://img.shields.io/badge/Spring-Boot-6DB33F?logo=spring&logoColor=white)
![Go](https://img.shields.io/badge/Go-1.23+-00ADD8?logo=go&logoColor=white)
![GoZero](https://img.shields.io/badge/GoZero-Framework-00ADD8?logo=go&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-20+-339933?logo=node.js&logoColor=white)
![NestJS](https://img.shields.io/badge/NestJS-Framework-E0234E?logo=nestjs&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi&logoColor=white)

## 目录

<details>
<summary>点击展开目录</summary>

- [描述](#描述)
- [功能说明](#功能说明)
- [设计图](#设计图)
- [技术栈](#技术栈)
- [第三方服务](#第三方服务)
- [环境要求](#环境要求)
- [环境设置](#环境设置)
- [环境配置脚本](#环境配置脚本)
- [Docker 基础中间件容器部署](#docker-基础中间件容器部署)
- [编译和运行项目](#编译和运行项目)
- [测试说明](#测试说明)
- [运行脚本配置](#运行脚本配置)
- [生产环境部署](#生产环境部署)
- [Docker 容器部署](#docker-容器部署)
- [Docker Compose 部署](#docker-compose-部署)
- [基础服务组件初始化](#基础服务组件初始化)
- [环境变量配置文件](#环境变量配置文件)
- [Swagger 说明](#swagger-说明)
- [项目规范说明](#项目规范说明)
- [项目可用工具说明](#项目可用工具说明)
- [其他说明](#其他说明)
- [许可证](#许可证)

</details>

## 描述

这是一个基于多语言技术栈构建的 IT 智能文章推荐与知识问答系统，主要包含以下框架：

- Spring（Java）
- GoZero（Go）
- NestJS（Node.js）
- FastAPI（Python）

所有服务通过 SpringCloud Gateway 统一网关进行访问，实现了服务治理、认证授权等功能。

[前端对应仓库地址](https://gitee.com/chu-shichao/react-web-demo)

## 功能说明

1. 基于 SpringBoot 和 MybatisPlus 实现文章发布、修改等操作，文章的创建和显示都支持 Markdown
2. 基于 SpringBoot 和 MybatisPlus 实现用户、分类、评论、点赞、收藏、关注等业务模块
3. 基于 SpringBoot 和 Redis 进行文章分类，用户状态/Token的管理操作
4. 基于 SpringBoot 和 AOP 技术权限校验实现用户端和管理端
5. 基于 SpringCloud Gateway 和 JWT 实现 API 网关的统一认证和权限控制
6. 基于 Redis Token Bucket 算法在网关层实现 API 限流和防刷功能
7. 基于 GoZero 和 ElasticSearch 进行搜索引擎式文章搜索
8. 基于 GoZero 和 GORM/sqlx 实现文章相关数据获取和同步（双 ORM 并存）
9. 基于 GoZero 和 WebSocket/SSE 实现用户实时聊天功能和消息通知
10. 基于 NestJS 和 Mongoose 进行文章操作日志和 API 日志的查看和分析
11. 基于 NestJS 和 TypeORM 实现文章下载的文章和用户数据获取
12. 基于 FastAPI 和 ClickHouse 技术栈实现系统数据的相关分析
13. 基于 FastAPI 和 SQLAlchemy 进行文章相关数据的获取和同步
14. 基于 FastAPI 和 LangChain 实现 RAG 文章检索增强和 Tools 调用 SQL 和 MongoDB，支持 **GPT/Gemini/DeepSeek** 进行多模型选择

## 设计图

- 系统架构图

  ![architecture](./static/pic/architecture.drawio.png)

- ER 图

  ![er](./static/pic/er.drawio.png)

## 技术栈

- SpringBoot：Java 后端框架，支撑系统核心业务服务
- GoZero：Golang 后端框架，支持系统高并发服务
- NestJS：Node.js 后端框架，支撑系统日志处理服务
- FastAPI：Python 后端服务，支撑系统数据分析和 Agent 服务
- Spring Cloud Gateway：API 网关
- JWT：身份验证
- Nacos：服务发现与配置中心
- MySQL：关系型数据库，系统核心数据库
- PostgreSQL：RAG 向量数据库
- MongoDB：非关系型数据库，系统日志数据库
- ElasticSearch：搜索引擎，系统搜索优化
- Redis：缓存服务和状态管理
- RabbitMQ：异步消息队列
- ClickHouse：大数据存储与分析
- WebSocket：用户实时聊天
- SSE：实时通知未读消息
- LangChain：大模型调用和 RAG 框架

## 第三方服务

- [阿里云百炼平台](https://bailian.console.aliyun.com/)
- [Close AI](https://platform.closeai-asia.com/dashboard)
- [阿里云 OSS](https://oss.console.aliyun.com/overview)

## 环境要求

- Java 17+
- Maven 3.6+
- Gradle 9.3+(可选，但推荐用于 Java 项目构建)
- Go 1.23+
- Node.js 20+
- Bun 1.2+(可选)
- Python 3.12+
- uv 0.9+(可选)
- MySQL 8.0+
- PostgreSQL + pgvector 15.4+
- MongoDB 5.0+
- ElasticSearch 7.12.1+
- Redis 6.0+
- RabbitMQ 3.8+
- ClickHouse 21.8+(可选)

## 环境设置

> **提示**: 推荐使用 `setup.sh` 配置脚本自动完成以下所有安装步骤。
>
> 如果需要手动配置，可以按照下面的步骤逐个模块进行。

### Spring 部分

```bash
cd spring # 进入文件夹
cd gateway # 进入网关
mvn clean install # 下载依赖
gradle wrapper # 生成项目专用 Gradle，运行自动下载依赖
```

### GoZero 部分

```bash
cd gozero/app # 进入文件夹
go mod tidy # 安装依赖
go install github.com/zeromicro/go-zero/tools/goctl@latest # 安装 goctl 代码生成工具
```

### NestJS 部分

```bash
cd nestjs # 进入文件夹
npm install # 安装npm包
bun install # 或者使用bun安装
```

### FastAPI 部分

```bash
# 使用标准 venv 和 requirements.txt
cd fastapi
# 创建虚拟环境
python3 -m venv venv
# 激活虚拟环境
source venv/bin/activate
# 安装依赖
pip install -r requirements.txt

# 使用 uv 进行项目管理
cd fastapi
# 配置 uv 虚拟环境
uv venv --python /usr/bin/python3.11 # 创建虚拟环境时指定 Python
# 激活虚拟环境
source .venv/bin/activate
# 同步依赖（可以使用国内镜像）
uv sync
```

> 项目使用 uv 进行依赖管理，配置文件为 `pyproject.toml`。镜像源配置在 `~/.config/uv/uv.toml`，内容如下

```toml
[[index]]
name = "aliyun"
url = "https://mirrors.aliyun.com/pypi/simple"
default = true

```

## 环境配置脚本

为了简化项目初始化过程，我们提供了自动化配置脚本 `scripts/setup.sh`，可以自动检测环境、安装依赖并配置所有模块。

### Linux/macOS 使用方式

```bash
# 1. 使用便捷脚本调用（推荐）
./mix setup

# 或直接调用
./scripts/setup.sh
```

### 交互式配置

运行脚本后会出现以下交互界面：

```bash
# 根据提示选择要配置的模块
# 选项:
# 1) Spring      - 配置 SpringBoot 服务
# 2) GoZero      - 配置 GoZero 服务
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
   - Spring: 自动检测是否有全局 Gradle 和 Maven，优先使用 Gradle（若两者都存在）；同时安装两者的依赖以确保完整性
   - Gateway: 支持 Gradle 和 Maven 两种构建工具

- GoZero: 自动安装 goctl（API/ORM 代码生成工具、API-First 方式代码生成和 Swagger 文档生成工具）
- FastAPI: 自动安装 uv 并自动创建 uv 虚拟环境并使用阿里镜像源加速安装

5. **目录自动创建**

- 自动创建 logs 目录（spring、gozero、nestjs、fastapi）
- 自动创建 static 目录（pic、excel、word）

### 脚本执行流程

```bash
./mix setup
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

1. **配置各服务的环境变量文件**（见下方"配置文件说明"章节，先参考 `.env.example` 生成本地 `.env`，Docker 则使用 `.env.docker`）
2. **启动基础服务**（MySQL、Redis、MongoDB、ElasticSearch、RabbitMQ、Nacos）
3. **使用运行脚本启动服务**（见"运行脚本配置"章节）

## Docker 基础中间件容器部署

项目提供了基础依赖容器部署脚本，用于快速创建和管理 MySQL、PostgreSQL、Redis、MongoDB、ElasticSearch、Nacos 和 RabbitMQ 等服务，供下方微服务部署使用。

### 基础容器部署命令

`mix docker-services` 用于创建、启动、查看和清理基础中间件容器；下面的 `Docker 容器部署` 章节才是应用服务编排内容。

```bash
# 创建所有容器
./mix docker-services up

# 查看容器状态
./mix docker-services status

# 查看容器日志
./mix docker-services logs <service>

# 停止所有容器
./mix docker-services stop

# 删除所有容器
./mix docker-services delete

# 显示帮助信息
./mix docker-services help
```

### 创建的容器服务

脚本会自动创建以下 Docker 容器（密码均为默认值，可通过 `.env` 文件自定义）：

| 服务              | 端口        | 用户名   | 默认密码 | 说明                     |
| ----------------- | ----------- | -------- | -------- | ------------------------ |
| **MySQL**         | 3306        | root     | 123456   | 关系型数据库             |
| **PostgreSQL**    | 5432        | postgres | 123456   | 向量数据库(含 pgvector)  |
| **Redis**         | 6379        | -        | 123456   | 缓存服务                 |
| **MongoDB**       | 27017       | root     | 123456   | 非关系型数据库           |
| **ClickHouse**    | 8123, 9002  | hcsy     | 123456   | 大数据分析数据库         |
| **ElasticSearch** | 9200, 9300  | -        | -        | 搜索引擎(7.12.1)         |
| **Nacos**         | 8848, 9848  | -        | -        | 服务发现与配置中心       |
| **RabbitMQ**      | 5672, 15672 | hcsy     | 123456   | 消息队列(管理界面 15672) |

### 自定义密码配置

所有容器密码均支持通过项目根目录 `.env` 文件自定义，脚本会优先读取 `.env` 中的变量，未设置时使用默认值：

```bash
# .env 文件示例
DB_PASSWORD=你的数据库密码          # MySQL 和 PostgreSQL 密码
REDIS_PASSWORD=你的Redis密码        # Redis 密码
MONGO_PASSWORD=你的MongoDB密码      # MongoDB 密码
CLICKHOUSE_USER=hcsy               # ClickHouse 用户名
CLICKHOUSE_PASSWORD=你的密码        # ClickHouse 密码
RABBITMQ_USER=hcsy                 # RabbitMQ 用户名
RABBITMQ_PASSWORD=你的密码          # RabbitMQ 密码
```

### 数据持久化目录

| 服务          | 宿主机目录                                     |
| ------------- | ---------------------------------------------- |
| MySQL         | `~/mysql/data`, `~/mysql/conf`, `~/mysql/init` |
| PostgreSQL    | `~/pgdata`                                     |
| Redis         | `~/redis_data`                                 |
| MongoDB       | `~/mongo_data`                                 |
| ClickHouse    | `~/clickhouse/data`, `~/clickhouse/logs`       |
| ElasticSearch | Docker Volume:`es-data`, `es-plugins`          |
| RabbitMQ      | Docker Volume:`mq-plugins`                     |

### 注意事项

- **首次创建**: 首次执行 `docker-services up` 时会自动创建 Docker 网络 `hcsy` 和所有数据持久化目录
- **数据持久化**: 所有容器的数据都会持久化到宿主机目录
- **密码配置**: 建议在 `.env` 文件中统一配置密码，避免使用默认密码
- **ElasticSearch**: 首次创建后会提示是否安装 IK 分词器（可选）
- **ClickHouse**: 端口 9002 映射到容器内 9000（避免与其他服务冲突），需设置 `ulimit nofile=262144`
- **Nacos**: 自动生成 `nacos/custom.env` 配置文件，MySQL 密码与 `DB_PASSWORD` 同步
- **权限问题**: 如果遇到权限错误，可能需要使用 `sudo` 或将用户加入 docker 组
- 如果有额外创建的组件，按照个人的配置改动配置文件

## 编译和运行项目

> 每个服务都可以独立运行：

### Spring 服务（包括 gateway 网关）

**使用 Maven 运行**：

```bash
# 运行Spring服务
cd spring
mvn clean install # 构建项目
mvn spring-boot:run # 启动项目

# 运行网关服务
cd gateway
mvn clean install # 构建项目
mvn spring-boot:run # 启动项目
```

**使用 Gradle 运行（推荐）**：

```bash
# 运行Spring服务
cd spring
gradle bootRun # 启动项目

# 网关服务
cd gateway
gradle bootRun # 启动项目
```

### GoZero 服务

```bash
# 运行 GoZero 服务
cd gozero/app
go build -o bin/gozero main.go # 构建项目
go run main.go # 运行项目
```

### NestJS 服务

**使用 npm 运行**：

```bash
# 运行NestJS服务
cd nestjs
npm run node:start # npm development 模式运行
npm run node:start:dev # npm watch 模式运行
npm run node:start:debug # npm debug 模式运行
npm run node:start:prod # npm production 模式运行
```

**使用 bun 运行**：

```bash
cd nestjs
npm run bun:start # bun 运行
npm run bun:dev # bun watch 模式运行
npm run bun:prod # bun production 模式运行
```

### FastAPI 服务

**使用 venv 运行**：

```bash
# 运行FastAPI服务
cd fastapi
source venv/bin/activate # 激活虚拟环境
python main.py
```

**使用 uv 运行**：

```bash
# 运行FastAPI服务
cd fastapi
uv run python main.py

# 或指定 Python 版本
uv run --python 3.12 python main.py
```

## 测试说明

本项目按服务拆分测试代码，各服务的测试入口和运行方式如下。

### 测试运行方式

1. Spring

```bash
cd spring
mvn test
```

只运行某个测试：

```bash
export INTERNAL_TOKEN_TEST_TOKEN=实际Token
cd spring
mvn -Dtest=InternalTokenUtilTest test
```

2. GoZero

```bash
cd gozero/app
go test ./...
```

只运行某个测试：

```bash
export INTERNAL_TOKEN_TEST_TOKEN=实际Token
cd gozero/app
go test ./common/utils -run 'TestGenerateInternalToken|TestValidateInternalToken' -v
```

3. NestJS

```bash
cd nestjs
npm test
```

只运行某个测试：

```bash
export INTERNAL_TOKEN_TEST_TOKEN=实际Token
cd nestjs
npx jest src/common/utils/internalToken.util.spec.ts
```

4. FastAPI

```bash
cd fastapi
pytest
```

只运行某个测试：

```bash
export INTERNAL_TOKEN_TEST_TOKEN=实际Token
cd fastapi
pytest tests/core/auth/test_internal_token.py
```

### 测试代码规范

1. **Spring**：测试文件放在 `spring/src/test/java` 下，命名建议使用 `*Test.java`。
2. **GoZero**：测试文件放在同包目录下，命名使用 `_test.go`，测试函数使用 `TestXxx`。
3. **NestJS**：测试文件放在 `nestjs/src` 下，命名使用 `*.spec.ts`，默认使用 Jest。
4. **FastAPI**：测试文件放在 `fastapi/tests` 下，命名使用 `test_*.py`，默认使用 pytest。
5. **其他说明**：生成测试参数可以写死在代码中，但是敏感信息的参数建议使用环境变量提供。

## 运行脚本配置

所有运行脚本已组织到 `scripts/` 目录中，便于项目管理和维护。

### 快速启动（推荐）

#### Linux/macOS

```bash
# 查看帮助信息
./mix help

# ===== 开发环境 =====
# 使用多窗格 tmux 布局启动所有服务（推荐用于开发调试）
./mix multi

# 使用顺序窗口模式启动所有服务
./mix seq

# 停止所有 tmux 服务
./mix stop

# ===== Seq 模式下使用指定构建工具启动服务 =====
# 使用 Gradle 构建并启动 Java 服务（推荐，更快）
./mix seq --java-build gradle

# 使用 Maven 构建并启动 Java 服务
./mix seq --java-build maven

# 使用 Bun 启动 NestJS 服务（推荐，比 npm 快）
./mix seq --node-runtime bun

# 使用 npm 启动 NestJS 服务
./mix seq --node-runtime npm

# 使用 UV 启动 FastAPI 服务（推荐，比 python 快）
./mix seq --python-runtime uv

# 使用 Python 启动 FastAPI 服务
./mix seq --python-runtime python

# 交互式模式：让用户选择构建工具
./mix seq -i

# ===== GoZero 代码生成 =====
./mix goctl-api
./mix goctl-orm

# ===== Docker 容器环境 =====
# 构建并启动所有微服务容器
./mix docker up

# 构建并启动特定服务容器
./mix docker up spring gozero

# 仅构建镜像
./mix docker build

# 推送所有镜像到远程仓库
./mix docker push --prefix docker.io/yourname

# 推送指定服务镜像到远程仓库
./mix docker push --prefix registry.example.com/team --tag v1.0.0 spring gozero

# 查看容器状态
./mix docker status

# 查看容器日志
./mix docker logs spring

# 停止所有容器
./mix docker stop

# ===== 生产环境 =====
# 构建所有服务到 dist/ 目录
./mix build

# 启动所有已构建的服务（后台运行）
./mix start

# 启动指定的服务
./mix start spring gateway
./mix start fastapi gozero

# 查看已构建服务的运行状态
./mix status

# 查看指定服务的运行状态
./mix status spring gozero

# 重启所有已构建的服务
./mix restart

# 重启指定的服务
./mix restart fastapi
./mix restart spring gateway nestjs

# 停止所有已构建的服务
./mix stop-dist

# 停止指定的服务
./mix stop-dist spring fastapi

# 查看服务的最新日志（只支持查看单个服务）
./mix logs spring
./mix logs fastapi
./mix logs gozero
```

**构建工具参数说明**：

- `--java-build gradle|maven`：选择 Java 构建工具（Spring/Gateway）
  - `gradle`：使用 Gradle（推荐，更快）
  - `maven`：使用 Maven（可选）
  - 默认值：`gradle`（如果已安装）

- `--node-runtime bun|npm`：选择 Node.js 运行时（NestJS）
  - `bun`：使用 Bun（推荐，比 npm 快 4-8 倍）
  - `npm`：使用 npm（可选）
  - 默认值：`bun`（如果已安装）

- `--python-runtime uv|python`：选择 Python 运行时（FastAPI）
  - `uv`：使用 UV（推荐，更快且支持虚拟环境）
  - `python`：使用原生 Python（可选）
  - 默认值：`uv`（如果已安装）

- `-i`/`--interactive`：交互式模式，让用户选择每个服务的工具

#### Windows

```powershell
# 启动所有服务（PowerShell）
PowerShell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

### 直接调用脚本

如果需要直接调用 `scripts/` 目录下的脚本：

#### Linux/macOS

```bash
# 启动服务（多窗格布局） - 使用 Gradle 构建
./scripts/run_multi.sh

# 或指定构建工具参数（推荐）
./scripts/run.sh --java-build gradle --node-runtime bun --python-runtime uv

# 启动服务（顺序窗口布局）
./scripts/run.sh

# 交互式选择工具
./scripts/run.sh -i

# 停止所有服务
./scripts/stop.sh

# 构建所有服务
./scripts/build.sh

# 管理分布式部署的服务

# 启动所有服务或指定服务
./scripts/dist-control.sh start              # 启动所有
./scripts/dist-control.sh start spring gozero   # 启动指定

# GoZero 代码生成
./scripts/goctl-api-init.sh
./scripts/goctl-orm-init.sh

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

**run.sh 脚本参数**：

| 参数                   | 选项               | 说明                                             |
| ---------------------- | ------------------ | ------------------------------------------------ |
| `--java-build`         | `gradle` / `maven` | Java 项目构建工具（Spring/Gateway），默认 gradle |
| `--node-runtime`       | `bun` / `npm`      | Node.js 运行时（NestJS），默认 bun               |
| `--python-runtime`     | `uv` / `python`    | Python 运行时（FastAPI），默认 uv                |
| `-i` / `--interactive` | 无                 | 交互式模式，提示用户选择各服务的工具             |
| `-h` / `--help`        | 无                 | 显示帮助信息                                     |

示例：

```bash
# 使用 Maven 和 npm 启动
./scripts/run.sh --java-build maven --node-runtime npm

# 使用 Python 启动 FastAPI
./scripts/run.sh --python-runtime python

# 交互式选择
./scripts/run.sh --interactive
```

#### Windows

```powershell
# 启动所有服务
.\scripts\run.ps1
```

### 脚本说明

| 脚本                        | 位置       | 功能                                       | 适用系统    |
| --------------------------- | ---------- | ------------------------------------------ | ----------- |
| `mix`                       | 项目根目录 | 便捷启动器，用于快速调用 scripts/ 下的脚本 | Linux/macOS |
| `run_multi.sh`              | scripts/   | 使用 tmux 多窗格布局启动所有服务（推荐）   | Linux/macOS |
| `run.sh`                    | scripts/   | 使用 tmux 顺序窗口模式启动所有服务         | Linux/macOS |
| `stop.sh`                   | scripts/   | 停止所有 tmux 服务                         | Linux/macOS |
| `build.sh`                  | scripts/   | 编译所有服务到 dist/ 目录                  | Linux/macOS |
| `dist-control.sh`           | scripts/   | 管理打包后的分布式服务（支持服务指定）     | Linux/macOS |
| `docker-services.sh`        | scripts/   | 创建、启动、停止和清理基础中间件容器       | Linux/macOS |
| `docker-compose-up.sh`      | scripts/   | 使用 Docker Compose 启动应用服务           | Linux/macOS |
| `docker-compose-down.sh`    | scripts/   | 使用 Docker Compose 停止应用服务           | Linux/macOS |
| `build_and_run_services.sh` | scripts/   | 构建并运行服务容器                         | Linux/macOS |
| `docker-push-images.sh`     | scripts/   | 将已构建的 Docker 镜像推送到远程仓库       | Linux/macOS |
| `setup.sh`                  | scripts/   | 环境初始化和依赖安装                       | Linux/macOS |
| `swag-init.sh`              | scripts/   | 生成 GoZero Swagger 文档                   | Linux/macOS |
| `goctl-api-init.sh`         | scripts/   | 生成 GoZero API 代码                       | Linux/macOS |
| `goctl-orm-init.sh`         | scripts/   | 生成 GoZero ORM 代码                       | Linux/macOS |
| `run.ps1`                   | scripts/   | PowerShell 脚本，启动所有服务              | Windows     |

### 服务名称

dist-control.sh 和 mix 支持以下服务名称：

- `spring` - SpringBoot 服务
- `gateway` - Spring Cloud Gateway 网关服务
- `fastapi` - FastAPI 服务
- `gozero` - GoZero 服务
- `nestjs` - NestJS 服务

如不指定服务名称，则对所有服务进行操作。

### 注意事项

1. **tmux 依赖**：Linux/macOS 脚本依赖 `tmux`，请确保已安装
2. **执行权限**：Linux/macOS 脚本需要执行权限，可以通过 `chmod +x scripts/*.sh` 来设置
3. **相对路径**：所有脚本都使用相对路径，可以在任何目录下调用项目的脚本
4. **服务依赖**：启动前请确保 MySQL、Redis、MongoDB、ElasticSearch、RabbitMQ、Nacos 等基础服务已运行
5. **logs 命令**：仅支持查看单个服务的日志，如需查看多个服务请依次调用

## 生产环境部署

本项目提供了统一的打包和部署脚本，可以一键打包所有微服务并统一管理。

**方法一：使用便捷脚本**

```bash
# 1. 一键打包所有服务
./mix build

# 2. 启动所有服务
./mix start

# 3. 查看服务状态
./mix status

# 4. 重启所有服务（代码更新后）
./mix restart

# 5. 停止所有服务
./mix stop-dist
```

**方法二：直接调用脚本**

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

- **mix**（项目根目录）
  - 便捷启动器，用于快速调用 `scripts/` 下的脚本
  - 支持开发环境和生产环境命令

- **scripts/build.sh**
  - 编译所有服务：Spring、Gateway、FastAPI、GoZero、NestJS
  - 将编译结果打包到 `dist/` 目录
  - 包含编译错误检查和日志输出

- **scripts/dist-control.sh**
  - 管理打包后的分布式服务
  - 支持的操作：`start`、`stop`、`status`、`restart`、`logs`

## Docker 容器部署

项目提供了完整的 Docker 支持，可以为每个微服务构建镜像并创建容器。

### 微服务 Docker 快速开始

```bash
# 1. 构建并启动所有微服务容器
./mix docker up

# 2. 查看容器状态
./mix docker status

# 3. 查看特定服务的日志
./mix docker logs spring

# 4. 停止所有微服务容器
./mix docker stop
```

Docker 环境会优先读取每个服务目录下的 `.env.docker`，不会自动创建该文件。请根据需要手动准备 Docker 专用环境变量文件，本地开发仍然使用 `.env`。

Docker 启动时会把所有应用容器接入同一个 `hcsy` 网络，容器间地址请使用服务名：

- `gateway` -> `8080`
- `spring` -> `8081`
- `gozero` -> `8082`
- `nestjs` -> `8083`
- `fastapi` -> `8084`

基础组件在同一网络中的服务名为：

- `mysql`
- `redis`
- `mongodb`
- `es`
- `nacos`
- `mq`
- `pgvector-db`
- `clickhouse`

### 微服务容器说明

| 服务        | 端口 | 镜像名称             | 容器名称                | 技术栈           |
| ----------- | ---- | -------------------- | ----------------------- | ---------------- |
| **Gateway** | 8080 | `mix-gateway:latest` | `mix-gateway-container` | Java 17 + Alpine |
| **Spring**  | 8081 | `mix-spring:latest`  | `mix-spring-container`  | Java 17 + Alpine |
| **GoZero**  | 8082 | `mix-gozero:latest`  | `mix-gozero-container`  | Go 1.23 + Alpine |
| **NestJS**  | 8083 | `mix-nestjs:latest`  | `mix-nestjs-container`  | Node 20 + Alpine |
| **FastAPI** | 8084 | `mix-fastapi:latest` | `mix-fastapi-container` | Python 3.12      |

### 高级用法

```bash
# 仅构建特定服务的镜像
./mix docker build spring gozero

# 仅构建镜像，不启动容器
./scripts/build_and_run_services.sh --build-only

# 手动启动容器时指定配置文件
docker run -d --name mix-spring-custom \
  --network hcsy \
  -p 8081:8081 \
  -v $(pwd)/spring/application.yaml:/app/application.yaml \
  -v $(pwd)/spring/application-secret.yaml:/app/application-secret.yaml \
  mix-spring:latest

# 查看容器日志
docker logs -f mix-spring-container

# 进入容器交互式终端
docker exec -it mix-spring-container bash

# 重启容器（应用新配置）
docker restart mix-spring-container
```

## Docker Compose 部署

目前 `docker-compose.yml` 仅包含 5 个应用服务：

- gateway
- spring
- gozero
- nestjs
- fastapi

第三方依赖（MySQL/Redis/MongoDB/ES/Nacos/RabbitMQ/ClickHouse）请继续使用现有启动脚本（如 `./scripts/docker-services.sh`），并确保它们与同一 Docker 网络 `hcsy` 运行。

应用容器镜像将由 `./mix docker build` 生成：

```bash
./mix docker build gateway spring gozero nestjs fastapi
```

为了与 `mix docker` 启动一致，`docker-compose` 会挂载以下配置与日志目录：

- `spring/application.yaml -> /app/application.yaml`
- `gozero/etc -> /app/etc`
- `nestjs/application.yaml -> /app/application.yaml`
- `fastapi/application.yaml -> /app/application.yaml`
- `logs/<service> -> /app/logs/<service>`
- `static/pic`, `static/excel`, `static/upload`

`./scripts/docker-compose-up.sh` 已自动创建目录并设置可写权限，避免 `ENOENT application.yaml` 与 `permission denied` 问题。

建议先构建镜像，再启动 Compose。

### 前置要求

- **Docker**：>= 20.10
- **docker-compose**：或使用 `docker compose` (Docker CLI 集成)

### 启动服务

```bash
# 启动依赖服务（如果尚未启动）
./scripts/docker-services.sh

# 启动应用服务（5 个）
./mix compose up
```

### 停止服务

```bash
./mix compose down
```

### 状态查看

```bash
./mix compose status
```

### 查看日志

```bash
./mix compose logs <service>
```

### 手动命令（可选）

```bash
docker-compose up -d --build
docker-compose down -v
```

### 文件说明

- `docker-compose.yml`：整套应用编排（数据库、缓存、消息队列、服务容器）
- `scripts/docker-compose-up.sh`：快速启动脚本
- `scripts/docker-compose-down.sh`：快速停止脚本
- `scripts/docker-services.sh`：创建和管理基础中间件容器
- `scripts/build_and_run_services.sh`：构建并运行服务容器

### 访问服务

服务启动后可直接访问本地端口：

- Gateway: http://localhost:8080
- Spring: http://localhost:8081
- GoZero: http://localhost:8082
- NestJS: http://localhost:8083
- FastAPI: http://localhost:8084

### 高级用法

```bash
# 查看某个服务实时日志
./mix compose logs spring

# 查看所有服务状态
./mix compose status

# 重启某个服务（可配合 docker-compose restart）
cd /home/hongch666/mix-web-demo
sudo docker-compose -f docker-compose.yml restart spring

# 进入容器调试
sudo docker exec -it mix-spring /bin/bash

# 清理未用镜像与容器
docker system prune -af
```

## 基础服务组件初始化

### 确保已安装并启动以下数据库服务：

- MySQL
- PostgreSQL
  - 需要安装 `pgvector`插件
- MongoDB
- Redis
- ElasticSearch
- RabbitMQ
- Nacos

### SQL 初始化脚本说明

项目的 SQL 初始化脚本已经统一迁移到根目录的 `db/` 目录下，按数据库类型拆分管理。

- `db/mysql/`：MySQL 建表脚本，按表拆分为独立文件
- `db/postgresql/`：PostgreSQL 初始化脚本，主要用于扩展启用
- `db/clickhouse/`：ClickHouse 初始化脚本，主要用于映射库和物化视图

建议执行顺序如下：

1. 先执行 `db/mysql/` 下的建表脚本
2. 再执行 `db/postgresql/` 下的扩展脚本
3. 最后执行 `db/clickhouse/` 下的同步脚本

如果后续新增数据库初始化内容，也请继续放到 `db/` 下对应的数据库目录中，便于统一维护和查找

### MySQL 表创建

系统服务会自动创建，也可以先执行 `db/mysql/` 下的SQL脚步创建基础表结构

### PostgreSQL 表创建

LangChain 会自动创建，但需要先执行 `db/postgresql/extensions.sql` 启用 `pgvector` 扩展

### MongoDB 表创建

数据库为 `demo`，集合为 `articlelogs`和 `apilogs`，系统会自动创建

### ElasticSearch 索引创建

无需创建，系统同步数据时会自动创建，需要启动后触发 ElasticSearch 同步

### ClickHouse 创建

需要先执行 `db/clickhouse/articles_sync.sql`，其中包含 MySQL 映射库、本地表和物化视图的创建语句，MySQL 映射库需要修改为实际的 MySQL 连接信息

## 环境变量配置文件

本项目按环境拆分配置文件：

- `.env.example`：示例文件，保留全部变量名，用于复制生成本地配置
- `.env`：本地开发使用的真实配置文件，不建议提交敏感值
- `.env.docker`：Docker 容器使用的环境变量文件，脚本会在容器启动时读取它

所有配置值通过 `${VAR_NAME:default_value}` 的格式在 YAML 文件中引用。

### 各服务配置说明

各服务的具体环境变量请直接参考对应的 `.env.example`，这里不再重复列出完整配置。

- Spring：`spring/.env.example`、`spring/.env.docker`
- GoZero：`gozero/app/.env.example`、`gozero/app/.env.docker`
- NestJS：`nestjs/.env.example`、`nestjs/.env.docker`
- FastAPI：`fastapi/.env.example`、`fastapi/.env.docker`
- Gateway：`gateway/.env.example`、`gateway/.env.docker`

使用方式保持一致：

1. 先复制 `.env.example` 为本地 `.env`
2. 再按实际环境填写真实值
3. Docker 场景单独维护 `.env.docker`

### 环境变量使用说明

1. **密钥管理**: 所有密钥信息（数据库密码、API KEY、JWT Secret 等）不应该提交到版本控制系统，应该在本地 `.env` 文件中配置
2. **示例文件**: 新克隆项目后，先复制对应服务的 `.env.example` 为 `.env`，再填写真实值
3. **Docker 文件**: Docker 运行时读取 `.env.docker`，如果需要修改容器环境变量，请单独维护该文件，不要复用本地 `.env`
4. **YAML 中的引用格式**: 在各服务的 `application.yaml` 配置文件中，使用以下格式引用环境变量：

   ```yaml
   # YAML 中的使用示例
   server:
     port: ${SERVER_PORT:8080}
   database:
     host: ${DB_HOST:localhost}
     password: ${DB_PASSWORD:default-password}
   ```

5. **默认值**: 格式 `${VAR_NAME:default_value}` 中，冒号后面是默认值，当环境变量未设置时使用默认值
6. **加载顺序**: 本地启动时会自动从 `.env` 文件加载环境变量，Docker 启动时会读取 `.env.docker`，然后再解析 YAML 配置文件
7. **JWT 密钥说明**: 系统环境变量设置的 JWT 密钥至少为 32 位字符串

## Swagger 说明

> 启动时会显示对应的 swagger 地址

### Spring 部分

1. 在 config 包下的 `SwaggerConfig.java`中修改对应 Swagger 信息
2. 使用 `@Operation(summary = "spring自己的测试", description = "输出欢迎信息")`设置对应接口
3. 在 `http://[ip和端口]/swagger-ui/index.html`访问 Swagger 接口

### GoZero 部分

本项目已采用 **API-First** 方式管理 Swagger 文档，所有 API 定义统一存放在 `.api` 文件中，使用 goctl 的内置 Swagger 生成工具自动生成文档。

**使用方式：**

1. 在 `gozero/api` 目录下对应的 `.api` 文件中使用 `@doc` 注释定义 API

   ```api
   @doc(
       summary: "获取用户列表"
       description: "获取所有用户信息"
   )
   get /users returns (UserListResp)
   ```

2. 在 `gozero/app/main.go` 启动时会自动提供 Swagger UI
   - Swagger UI: `http://[ip和端口]:8082/swagger/index.html`

3. 每次修改 `.api` 文件后，运行以下命令重新生成 Swagger 文档：

   ```bash
   # 使用快捷方式
   ./mix swag

   # 或直接调用脚本
   cd gozero && bash script/swagger/genSwagger.sh
   ```

4. 生成的 Swagger 文件位于 `gozero/app/docs/` 目录
5. 目前 Swagger 文档的描述、作者、版本信息和中文分组等相关 Swagger 内容存在问题，使用 `/script/swager/fix.py` 脚本进行修复，修复后会覆盖原来的 Swagger 文件，如有需要可修改 `fix.py` 脚本中的相关内容

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

## 项目规范说明

> 这个为当前项目的代码和文件等相关规范，建议遵守

### 项目架构说明

1. Spring 项目采用通用的三层架构，`/controller`为对应接口，`/service`为对应实际逻辑（使用接口+实现形式），`/mapper`为对应数据库操作，并且使用依赖注入进行调用
2. GoZero 项目采用通用的三层架构，`/handler`为对应接口，`/logic`为对应实际逻辑，`/model`为对应数据库操作，并且使用 `svc`依赖注入进行调用
3. NestJS 项目采用默认的 module 划分格式，每个 module 有对应的 `xxx.controller.ts`、`xxx.service.ts`、`xxx.module.ts`文件，`/dto`、`/entities`、`/schema` 放置对应的 DTO 类、数据库实体类、Mongoose 实体类，并且使用依赖注入进行调用
4. FastAPI 项目采用官方推荐的目录结构，在app下实现代码，`api`路由接口，`services`服务逻辑，`crud`为对应数据库操作，`core`放置核心功能模块，并且基于 `Depend`函数和获取实例函数进行依赖注入调用

### 项目文件夹结构说明

1. Spring 项目将三层架构代码放置在 `/api`文件夹下，通用模块放置在 `/common`文件夹下，注解和配置相关放置在 `/core`文件夹下，基础设施相关放置在 `/infra`文件夹下，和实体相关的模块放在 `/entity`下，如 `/dto`、`/vo`、`/po`
2. GoZero 项目将 `.api`设计文件放置在 `/api`文件夹下，脚本放置在 `/scripts`文件夹下，生成的代码放置在 `/app`文件夹下，`/app` 下采用GoZero的设计方式，`/model`下放置数据库实体和操作，`/common`下放置通用代码模块，`/internal`下放置业务相关的代码模块，`/etc`下放配置文件，`/internal`文件夹下按照 `/handler`、`/logic`等GoZero的设计方式进行划分
3. NestJS 项目的通用工具放置在 `/common`下，module 相关的工具模块放置在 `/modules`下，接口相关的模块放置在 `/api`下，和系统相关的模块放置在 `/framework`下，如 `filters`、`guards`、`interceptors`等
4. FastAPI 项目的核心代码放置在 `/app`下，`api`下放置路由接口，`services`下放置服务逻辑，`crud`下放置数据库操作，`core`下放置核心功能模块，`/models`下放置实体相关的模块，`/schemas`下放置 Pydantic 模型
5. 其他相关的文件夹命名尽可能沿用当前项目的设计

### 项目文件命名说明

1. Spring 项目采用驼峰命名方式，如 `UserCreateDTO.java`
2. GoZero 项目采用驼峰命名方式，如 `userCreateDTO.go`
3. NestJS 项目采用点号命名和驼峰命名混合使用的方式，驼峰命名区分模块名，点号区分功能，如 `userCreate.dto.ts`
4. FastAPI 项目采用驼峰命名方式，如 `userCreateDTO.py`

### 返回格式说明

1. 返回统一使用 `application/json`格式返回，格式如下

   ```json
   {
     "code": 1,
     "data": Object,
     "msg": "success"
   }
   ```

- `code`为响应码，1 为成功，0 为失败
- `data`为实际数据，可以为空，一般是查询返回的结果
- `msg`为返回信息，成功一般为“success”，失败则为失败原因

2. 一般成功时除查询接口和部分状态管理外，其他接口都是无返回 `data`，即 `data`为 `null`
3. 失败时 `data`统一为 `null`，错误原因使用 `msg`参数
4. 无论成功还是失败，HTTP 的状态码均为 200

### 异常处理说明

1. Spring 项目使用全局异常处理类 `GlobalExceptionHandler.java` 进行异常捕获和处理，业务异常统一抛出 `BusinessException` 异常
2. GoZero 项目使用中间件 `recoveryMiddleware.go` 进行异常捕获和处理，业务异常统一抛出 `BusinessError` 异常
3. NestJS 项目使用全局异常过滤器 `all-exceptions.filter.ts` 进行异常捕获和处理，业务异常统一抛出 `BusinessException` 异常
4. FastAPI 项目使用 `exceptionHandlers.py` 下的全局异常处理函数进行异常捕获和处理，业务异常统一抛出 `BusinessException` 异常

### 常量说明

1. Spring 项目使用 `common/utils/Constants.java` 进行常量类管理，包括相关字符串和数字常量
2. GoZero 项目使用 `common/utils/constants.go` 进行常量管理，包括相关字符串和数字常量
3. NestJS 项目使用 `common/utils/constants.ts` 进行常量类管理，包括相关字符串和数字常量，当前模板字符串没有抽离常量
4. FastAPI 项目使用 `core/base/constants.py` 进行常量类管理，包括相关字符串和数字常量，当前模板字符串没有抽离常量

目前常量类均可根据需要进行扩展，尽可能使用常量类进行统一管理，避免硬编码。

### 定时任务说明

1. 统一使用 Cron 表达式的方式进行定时任务管理
2. 遵循当前项目的定时任务设置方式
3. 部分定时任务使用 `logic`封装定时任务的实际逻辑，在定时任务主文件调用 `logic`
4. 定时任务建议使用分布式锁时，锁 Key 的命名规范为 `lock:task:<业务>:<动作>`

### 其他说明

1. FastAPI 部分使用 `__init__.py`文件导出对应的函数/类，导入使用的时候以包为导入路径
2. FastAPI 部分需要在 app 创建时添加的相关组件（如 router、中间件、异常处理器）在 `__init__.py`导出对应列表或者字典，用于 app 创建时遍历添加
3. FastAPI 部分的 app 创建在 `app.py`的 `create_app`函数实现，lifespan 操作在 `lifespan.py`实现，主函数只进行调用和 `uvicorn`的启动
4. GoZero 部分的初始化在 `internel/boot` 文件夹创建，main 函数只进行调用，配置相关的初始化在 `svc` 文件夹下初始化执行
5. NestJS 项目的 app 创建在 `app`目录下的 `createApp`函数实现，main 函数只进行调用，`app`目录下包含 `app.module.ts`的 NestJS 的包初始化
6. Spring 项目的 Main 类只进行服务的启动，相关配置或初始化行为在 `config`目录下使用 `@Configuration`注解实现

## 项目可用工具说明

### 日志注解/中间件

1. Spring 项目使用 `@ApiLog` 注解 + `ApiLogAspect` 进行请求日志记录，并将日志发送到 RabbitMQ

- 机制: AOP 环绕切面获取请求方法/路径/参数，记录耗时并组装日志消息，最终写入日志并投递队列

2. GoZero 项目使用 `apiLogMiddleware` 中间件记录请求参数、路径、耗时，并发送 API 日志到 RabbitMQ，在 `handler`中使用 `ApplyApiLog` 函数启用日志记录

- 机制: 中间件读取请求上下文与请求体，计算耗时并发送日志消息到队列

3. NestJS 项目使用 `@ApiLog` 装饰器 + `ApiLogInterceptor` 记录日志并发送到消息队列

- 机制: 通过 Reflector 读取装饰器元数据，拦截请求提取参数与耗时，调用 MQ 服务发送日志

1. FastAPI 项目使用 `@log` 装饰器（支持 `ApiLogConfig`）记录请求日志，耗时统计并发送到 RabbitMQ

- 机制: 装饰器从 `Request` 提取方法/路径/参数，统计耗时，必要时包装流式响应并投递日志

### 权限校验注解/中间件

1. Spring 项目使用 `@RequirePermission` 注解 + `PermissionValidationAspect`，支持角色校验、allowSelf、自定义业务类型与参数来源

- 机制: 切面从 `UserContext` 取用户信息，解析路径/请求体参数，按业务类型与参数来源判断权限

2. GoZero 项目暂无通用权限注解，中间件 `InjectUserContext` 仅负责注入用户信息，权限校验主要在业务层处理

- 机制: 中间件只把 `X-User-Id`/`X-Username` 注入到上下文，具体权限由 service/handler 自行校验

3. NestJS 项目使用 `@RequireAdmin` 装饰器 + `RequireAdminGuard` 进行管理员权限校验

- 机制: Guard 读取装饰器元数据与 CLS 用户信息，调用用户服务判断是否管理员

4. FastAPI 项目使用 `@require_admin` 装饰器进行管理员权限校验

- 机制: 装饰器读取当前用户 ID 并查询用户角色，不满足条件抛出业务异常

### 内部服务令牌注解/中间件

1. Spring 项目使用 `@RequireInternalToken` 注解 + `InternalTokenAspect` 校验 `X-Internal-Token`，并通过 Feign `DefaultHeaderInterceptor` 自动注入内部令牌

- 机制: Feign 拦截器生成内部 JWT 并写入请求头，切面解析并校验令牌及服务名称

2. GoZero 项目使用 `InternalTokenMiddleware` 校验内部令牌，支持验证指定服务名称

- 机制: 中间件从请求头读取 JWT，校验签名/过期/服务名，失败直接中断请求

3. NestJS 项目使用 `@RequireInternalToken` 装饰器 + `InternalTokenGuard` 校验内部服务令牌

- 机制: Guard 从请求头提取 JWT，验证并检查指定服务名匹配

4. FastAPI 项目使用 `@requireInternalToken` 装饰器校验内部服务令牌，并支持指定服务名称

- 机制: 装饰器读取 `X-Internal-Token`，校验并将 claims 写入 `request.state`

### 服务间调用工具

1. Spring 项目使用 Feign 客户端 `FastAPIClient`/`GoZeroClient`/`NestjsClient` 调用其他服务，`DefaultHeaderInterceptor` 自动注入用户信息与内部令牌

- 机制: Feign 统一注入 `X-User-Id`/`X-Username` 与内部 JWT，实现服务间安全调用

2. GoZero 项目使用 `ServiceDiscovery.CallService`（Nacos 服务发现 + 负载均衡），自动注入用户信息与内部令牌

- 机制: 通过 Nacos 获取实例并轮询负载均衡，构建请求头后发起 HTTP 调用

3. NestJS 项目使用 `NacosService.call`（Nacos 服务发现 + axios），自动注入用户信息与内部令牌

- 机制: Nacos 发现实例，自动拼装请求头并用 axios 请求下游服务

4. FastAPI 项目使用 `call_remote_service`（Nacos 服务发现 + requests），自动注入用户信息与内部令牌

- 机制: 从 Nacos 获取服务实例，合并默认请求头后用 requests 发起调用

## 其他说明

### FastAPI Agent 工具说明

FastAPI 部分提供了基于 LangChain 的 AI Agent 工具，AI 模型可以通过这些工具进行数据查询和分析。

#### 1.SQL 数据库工具

通过 MySQL 数据库进行数据查询和分析：

| 工具名称            | 功能          | 参数            | 说明                                                                             |
| ------------------- | ------------- | --------------- | -------------------------------------------------------------------------------- |
| `get_table_schema`  | 获取表结构    | 表名(可选)      | 返回表的详细结构信息，包括列名、类型、主键、索引等；不提供表名则返回所有表的列表 |
| `execute_sql_query` | 执行 SQL 查询 | SQL SELECT 语句 | 仅支持 SELECT 查询，自动进行用户隔离过滤，返回最多 500 行数据                    |

#### 2.RAG 向量搜索工具

基于 PostgreSQL + Qwen 嵌入模型的文章向量搜索：

| 工具名称          | 功能         | 参数         | 说明                                                          |
| ----------------- | ------------ | ------------ | ------------------------------------------------------------- |
| `search_articles` | 向量语义搜索 | 问题或关键词 | 基于语义相似度搜索相关文章，返回相似度最高的 N 篇文章内容片段 |

#### 3.MongoDB 日志查询工具

查询系统日志和 API 调用记录：

| 工具名称                   | 功能     | 参数              | 说明                                          |
| -------------------------- | -------- | ----------------- | --------------------------------------------- |
| `list_mongodb_collections` | 列出集合 | 无                | 获取 MongoDB 中所有的 collection 及其基本信息 |
| `query_mongodb`            | 通用查询 | JSON 格式查询参数 | 查询任意 collection，支持条件过滤和结果限制   |

**MongoDB 查询参数格式示例：**

```json
{
  "collection_name": "api_logs",
  "filter_dict": { "user_id": 122, "status": { "$gte": 400 } },
  "limit": 20
}
```

#### 4.其他工具

- **意图路由工具 (intentRouter.py)**: 用于自动识别用户意图并路由到不同的处理模块
- **用户权限管理 (userPermissionManager.py)**: 管理和校验用户权限，实现细粒度访问控制

### 词云图说明

1. 词云图的字体应进行配置对应字体的路径

### 下载说明

1. Word 下载文件的模板路径在 NestJS 部分 yaml 配置文件中配置，使用 `${字段名}`进行模板书写，目前提供如下的示例
2. 内容示例

   ```word
   ${title}

   ${tags}

   ${content}
   ```

3. PDF 下载需要使用下面指令安装 `puppeteer`的 Chrome 浏览器

   ```bash
   npx puppeteer browsers install chrome
   ```

4. 当前 Word 下载只支持文章内容为纯文本，无法显示 Markdown 格式

### AI 说明

1. GPT/Gemini/DeepSeek 服务目前使用第三方平台 [Close AI](https://platform.closeai-asia.com/dashboard) ，根据说明文档进行配置
2. 嵌入模型使用的是[阿里云百炼平台](https://bailian.console.aliyun.com/)的嵌入模型
3. 上述的 API_KEY 应写在 `.env`中

### 用户聊天相关说明

1. GoZero 部分的用户聊天相关模块的用户 id 都是字符串，包括数据库存储，请求参数和返回参数

### AI 用户说明

1. AI 服务目前只有三种，对应数据库 `user` 表里面 `role` 为 `ai` 的用户，并且代码目前写死用户 id 为 1001/1002/1003；`db/mysql/user.sql` 里也已补充这三条 AI 用户初始化数据，重复执行会按 `id` 跳过已有记录。

### 邮箱说明

1. Spring 部分的邮箱登录使用 QQ 邮箱配置发送，需单独配置 QQ 邮箱授权码。

### Fresh 热启动工具说明

1. GoZero 服务若使用 `fresh`修改热启动工具，可以在配置对应配置文件用于修改编译结果产生位置，示例如下

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

### 搜索算法公式说明

1. GoZero 服务基于 ElasticSearch 实现的文章搜索采用综合评分算法，综合考虑多个维度的因素。
2. 综合评分公式

$$
\text{Score} = w_1 \cdot S_{es} + w_2 \cdot S_{ai} + w_3 \cdot S_{user} + w_4 \cdot S_{views} + w_5 \cdot S_{likes} + w_6 \cdot S_{collects} + w_7 \cdot S_{follow} + w_8 \cdot S_{recency}
$$

3. 其中：

- $S_{es} = \frac{1}{1 + e^{-x}}$（Sigmoid 归一化的 ElasticSearch 相关性分数，0-1 范围）
- $S_{ai} = \frac{\text{AI评分}}{10.0}$（0-1 范围，AI 评分范围为 0-10）
- $S_{user} = \frac{\text{用户评分}}{10.0}$（0-1 范围，用户评分范围为 0-10）
- $S_{views} = \min\left(\frac{\text{阅读量}}{\text{maxViewsNormalized}}, 1.0\right)$（阅读量归一化，0-1 范围）
- $S_{likes} = \min\left(\frac{\text{点赞量}}{\text{maxLikesNormalized}}, 1.0\right)$（点赞量归一化，0-1 范围）
- $S_{collects} = \min\left(\frac{\text{收藏量}}{\text{maxCollectsNormalized}}, 1.0\right)$（收藏量归一化，0-1 范围）
- $S_{follow} = \min\left(\frac{\text{作者关注数}}{\text{maxFollowsNormalized}}, 1.0\right)$（作者粉丝数归一化，0-1 范围）
- $S_{recency}$：文章新鲜度分数（基于创建时间）

4. 新鲜度计算公式

- 文章新鲜度采用高斯衰减函数，使时间离当前越近的文章得分越高：

$$
S_{\text{recency}} = e^{-\frac{(\Delta t)^2}{2\sigma^2}}
$$

- 其中：
  - $\Delta t$：文章创建时间与当前时间的差值（单位：天）
  - $\sigma$：时间衰减周期（默认 30 天）

- 高斯衰减函数具有以下特性：
  - 当 $\Delta t = 0$（刚发布）时，$S_{\text{recency}} = 1.0$（新鲜度最高）
  - 当 $\Delta t = 30$ 天时，$S_{\text{recency}} \approx 0.606$（衰减至约 60.6%）
  - 当 $\Delta t = 60$ 天时，$S_{\text{recency}} \approx 0.135$（衰减至约 13.5%）

- 权重配置说明

  | 默认权重分配（可在 GoZero 部分的 `.env` 中配置）： | 因素     | 权重                                          | 说明 |
  | -------------------------------------------------- | -------- | --------------------------------------------- | ---- |
  | ES 基础分数                                        | 0.25     | 关键词匹配的基础相关性（通过 Sigmoid 归一化） |      |
  | AI 评分                                            | 0.15     | 系统 AI 模型的内容质量评估（0-10 范围）       |      |
  | 用户评分                                           | 0.10     | 用户对文章的综合评价（0-10 范围）             |      |
  | 阅读量                                             | 0.08     | 文章的浏览热度                                |      |
  | 点赞量                                             | 0.08     | 用户的认可度                                  |      |
  | 收藏量                                             | 0.08     | 用户的收藏价值指数                            |      |
  | 作者关注数                                         | 0.04     | 作者的影响力                                  |      |
  | **文章新鲜度**                                     | **0.22** | **核心权重，近期发布的内容获得更高排名**      |      |
  - 权重总和为 1.0，确保评分结果的可比性和公平性。

## 许可证

本项目采用 [MIT 许可证](./LICENSE) 进行开源。

MIT 许可证允许：

- 自由使用、修改和分发
- 商业和个人用途
- 专利使用

详见 [LICENSE](./LICENSE) 文件
