---
name: mix-web-demo
description: mix-web-demo 多语言微服务仓库的编码规范总入口，含适用范围、项目内配套技能索引、任务路由与四服务通用规则。在本仓库生成或修改任何代码时必须先加载本入口，再按任务加载对应 mix-* 专项技能；与通用 skills 冲突时以本项目实证约定为准。
---

# mix-web-demo 项目专属编码规范（总入口）

## 适用范围

本仓库包含四个业务服务与一个网关，生成代码前必须先确认目标服务：

| 目录       | 技术栈                                                   | 端口 |
| ---------- | -------------------------------------------------------- | ---- |
| `spring/`  | Spring Boot 3 WebFlux + R2DBC + WebClient + Resilience4j | 8081 |
| `gozero/`  | go-zero 1.10 + rest/httpc + validator + sqlx             | 8082 |
| `nestjs/`  | NestJS + Fastify + Mongoose/TypeORM + opossum            | 8083 |
| `fastapi/` | FastAPI + SQLAlchemy async + contextvars + APScheduler   | 8084 |
| `gateway/` | Apache APISIX（配置驱动，无业务代码）                    | 8080 |

## 项目内配套技能

本规范已按主题拆分为多个 `mix-*` 技能，全部随仓库版本管理并经 `./mix skills` 同步到本机 Agent 技能目录。本入口只保留跨服务通用规则，专项细节按任务加载下列技能：

| 技能 | 何时加载 |
| ---- | -------- |
| `mix-db` | 建表、查询、索引设计与变更、`db/**` 脚本 |
| `mix-spring` | 修改 `spring/` 下代码 |
| `mix-gozero` | 修改 `gozero/` 下代码，含 `.api`/goctl 生成、搜索与实时链路 |
| `mix-nestjs` | 修改 `nestjs/` 下代码 |
| `mix-fastapi` | 修改 `fastapi/` 下代码 |
| `mix-gateway` | 修改 `gateway/` 下 APISIX 配置 |
| `mix-engineering` | 仓库工程、工具链、`mix` 命令、令牌与本地依赖环境 |
| `mix-docker` | Dockerfile、`.dockerignore`、镜像构建与分发 |
| `mix-workflow` | 接口变更收尾、内部接口清理、验证命令、测试、格式化与交付顺序 |

配套通用 skills（本仓库规范未覆盖的细节查阅它们，冲突时以本仓库专项技能为准）：

**Spring / Java**

- `springboot-patterns`、`spring-boot-engineer`：Spring WebFlux 响应式模式
- `java-spring-boot`、`java-springboot`：Spring Boot 模块划分与最佳实践

**NestJS / Node.js**

- `nestjs-patterns`、`nestjs-best-practices`、`nestjs-expert`：NestJS 模块、DI 与架构模式
- `nodejs-backend-typescript`：Node.js + TypeScript 后端通用约定

**FastAPI / Python**

- `fastapi-patterns`、`fastapi-expert`、`fastapi-python`：FastAPI 依赖注入与异步模式
- `python-backend`：Python 后端安全与代码质量
- `sqlalchemy-postgres`：SQLAlchemy 2.0 + Pydantic + PostgreSQL（FastAPI 侧的 ORM 与 pgvector 访问）

**Go / GoZero**

- `golang-design-patterns`、`golang-pro`：Go 组合根与并发模式
- `golang-code-style`：Go 代码风格与可读性约定
- `golang-database`：Go 数据库访问（sqlx 参数化查询、事务、连接池）
- `golang-error-handling`：Go 错误创建、包装与结构化日志
- `golang-testing`：Go 表驱动测试与 testify
- `golang-security`：Go 安全实践（注入防护、密钥管理、日志安全）

**数据库**

- `database-schema-design`、`database-migration`：Schema 设计与迁移（MySQL / PostgreSQL / MongoDB）

**AI / LLM**

- `langchain`、`llm-application-dev-langchain-agent`：LangChain Agent、工具调用与多模型编排
- `rag`：RAG 检索增强（pgvector 向量库与语义检索）

**工程化**

- `devops`：Docker / Docker Compose 部署与 CI/CD

## 任务路由

- 创建、修改、删除或评审测试，以及修复需要回归测试的缺陷：加载 `mix-workflow`，并完整读取其 `references/unit-testing.md`
- 接口新增/修改/删除：加载目标服务技能 + `mix-workflow`（文档生成与 Apifox 收尾）+ `mix-db`（若涉及表或索引）
- 改 Dockerfile / `.dockerignore` / 镜像发布：加载 `mix-docker`
- 改网关路由与插件：加载 `mix-gateway`
- 测试规范只约束测试边界与质量，不要求为了覆盖率测试生成代码、DTO、getter 或第三方库内部行为

## 通用规则（全部服务）

1. 使用中文回复；代码注释与字符串信息使用中文；注释与说明不含任何 emoji 与标志
2. 不主动生成任何文档，除非明确要求
3. SQL 一律参数化，禁止字符串拼接用户值。各服务占位风格：Spring R2DBC 用 `:param`；FastAPI ClickHouse 用 `%(name)s`；GoZero sqlx 用 `?`；NestJS 走 ORM 方法 API
4. **每次生成或修改代码后必须执行代码格式化与格式检查**：先跑 `./mix format <service>` 自动格式化，再跑 `./mix lint <service>` 确认检查通过，不允许把未格式化的代码交付；省略服务名时处理 spring、gozero、nestjs、fastapi 全部，`gateway` 为配置驱动不参与
5. **交付前必须验证编译通过**：格式与 lint 之后跑 `./mix compile <service>`（只编译校验，不产出打包目录），未通过不得交付；该步骤与「验证命令」章节里各服务的编译命令等价，省略服务名时处理四个服务全部。`./mix compile` 与打包命令 `./mix dist build` 职责不同，不要用后者替代前者（后者会清理 dist 并产出可运行产物）。对应工具未安装时该服务返回码 2 自动跳过，不允许据此判定通过
   - **Windows 环境下所有 `./mix` 命令与项目脚本统一用 Git Bash 执行**：从 PowerShell 启动时用 `& "C:\Program Files\Git\bin\bash.exe" -c "./mix format spring"`；不要直接用 PowerShell 跑 `./mix`，也不要用 WSL 的 `bash`（WSL 侧没有各服务工具链，会导致 gozero/fastapi 等被「工具未安装」跳过、NestJS 的 `tsc` 找不到 `node_modules/.bin` shim 而误报失败）。Git Bash 不可用时改用本机服务工具链直接验证（如 `go build ./...`、`node node_modules/typescript/bin/tsc --noEmit`、`python -m compileall`），并如实说明未跑 mix
6. 常量抽取：四个服务均有常量类，消息类字符串必须进常量类引用
   - Spring：`common/constants/`（`Messages`、`Defaults`、`RedisKeys`、`Scripts`、`SqlTools`、`HttpCode`、`HeaderNames`、`MetricNames`、`RabbitQueues`、`SyncResource`、`SyncAction`、`SyncChangeType`、`TelemetryConstants`、`WarehouseResources`）
   - NestJS：`common/constants/`（`Messages`、`HttpCode`、`Defaults`、`ErrorIds`、`RedisKey`、`SqlTools`、`MongoTools`、`Swagger`、`Telemetry`、`MetricNames`、`ExportTemplate`）
   - FastAPI：`core/constants/`（`Messages`、`Defaults`、`HttpCode`、`ErrorCodes`、`RedisKeys`、`Scripts`、`WarehouseScripts`、`Prompts`、`Algorithm`、`Intent`、`Vector`、`AiUsers`、`SwaggerConfig`、`Telemetry`、`MetricNames`）
   - GoZero：`app/common/constants/`（`messages.go`、`defaults.go`、`validations.go`、`httpCode.go`、`remoteCall.go`、`redisKeys.go`、`scripts.go`、`sqlTools.go`）
   - 语言支持字符串模板时（Python f-string、TS 模板串、Go fmt），动态部分用模板拼接常量，不把整句抽离
   - **常量类内部成员顺序：函数型成员必须全部排在普通常量之前**（NestJS 为 `static readonly NAME = (...) => ...` 形式的静态属性，FastAPI 为 `@staticmethod` 方法），新增常量时先写函数成员再写普通常量；该约定由 `./mix lint` 里的 `scripts/quality/constants.py` 检查并报错，`./mix format` 不做任何常量整理（Spring 与 GoZero 的常量前缀与其配套方法成对书写，只检查注释与分类，不参与顺序检查）
   - **常量注释与分类（四个服务统一）**：每个常量与每个函数型成员都必须带能被 IDE 悬停展示的注释，注释写在成员的声明处而不是集中写一块
     - Spring：成员上方 `/** 单行说明 */`（Javadoc），字段用单行形式，不需要 `@param` 之类的标签
     - NestJS：成员上方 `/** 单行说明 */`（JSDoc），与类、方法的 JSDoc 同一风格
     - GoZero：成员上方 `// 单行说明`，逐行注释，与 gofmt 对齐后的列宽无关
     - FastAPI：普通常量写在**变量下方**的三双引号字符串里（PEP 257 属性文档串，Pylance 与 PyCharm 会作为悬停说明展示），形如 `ARTICLE_TOP10: str = "article:top10"` 下一行写 `"""文章阅读量前十榜单的缓存 key"""`；`@staticmethod` 方法仍写在函数体内第一行
     - 成员按用途分类摆放，每个分类以单行分类注释开头：Java / NestJS / GoZero 用 `// ===== 分类名 =====`，FastAPI 用 `# ===== 分类名 =====`；分类注释与下方的成员注释之间空一行，分类内部不再拆散不相干的常量，Go 的 `const` / `var` 块把分类注释写在 `const (` 上方或块内首行均可
     - 注释内容说明该常量的用途、取值来源或与其它服务的对齐关系（如「需与 GoZero 侧 `SEARCH_GRAPH_CANDIDATE_LIMIT` 保持一致」），不复述常量名与字面值；结尾不加中文句号（见通用规则 13）
     - 该约定由 `./mix lint` 里的 `scripts/quality/constants.py` 检查：缺少成员注释、成员未归入任何分类都会报错并打印文件与行号
   - 注解 / 装饰器的字符串参数**不抽常量**，直接写字面量：这类字符串只在声明处使用一次，抽到常量类后需跳转查看，反而降低可读性
     - Spring：`@Operation(summary, description)`、`@Tag`、`@ApiLog("操作描述")`
     - NestJS：`@ApiOperation({ summary, description })`、`@ApiTags`、`@ApiLog("操作描述")`
     - FastAPI：`@router.get/post(..., summary=, description=)`、`@log("操作描述")`、`logWithConfig("操作描述")`、Pydantic `Field(description="...")`（含 Agent 工具参数模型与结构化输出模型），动态部分用 f-string / 字符串拼接把字面量与变量组合（如 `f"聚合结果返回条数上限，最大 {Defaults.MONGODB_AGGREGATE_MAX_DOCS}，服务端会强制收敛"`）
     - GoZero：`ApplyApiLog(rabbitPublisher, logger, handler, "操作描述")` 与 `ApplyApiLogSkipMq` 的描述参数同样直接写字面量，**不再新增 `API_LOG_*` 描述常量**；handler 模板生成时留下 `"待补充接口描述"` 占位，必须替换为具体文案
7. 相互独立的 IO 调用（RPC/HTTP/DB/Redis/ES/MQ）必须并行化，禁止串行等待；各服务并行原语见对应章节
8. 日志遵循各服务现有封装（见各服务章节），禁止绕过封装直接 print/console/logx 散用
9. 远程调用统一走各服务封装的客户端，自动透传用户上下文头：`X-User-Id`、`X-Username`、`X-Session-Id`、`Authorization`、`X-Internal-Token`；无登录用户时内部令牌 `userId=-1` 表示系统调用。禁止在新代码里裸用 httpx/axios/WebClient/http.Client 直连其他服务。各服务的唯一入口与底层 HTTP 客户端：
   - Spring：`infra/client/ServiceWebClient`（**WebClient** + `@LoadBalanced` 按服务名寻址 + Resilience4j 熔断/重试），按目标服务加方法
   - GoZero：`app/common/client` 的 `ServiceDiscovery.CallService`（**go-zero `rest/httpc`** + Nacos 轮询 + 退避重试），按目标服务在 `internal/client/` 封装
   - NestJS：`module/common/nacos/nacos.service.ts` 的 `call(opts)`（**axios** + axios-retry + opossum），按目标服务在调用方封装 Client 类
   - FastAPI：`app/core/client/client.py` 的 `call_remote_service`（**httpx** 共享连接池 + SimpleCircuitBreaker + tenacity），按服务在 `internal/clients/` 封装
   - **客户端只保留有生产调用方的方法（四个服务统一要求）**：不要照下游接口清单成批包装；只为单测存在或完全无引用的方法直接删掉，连同只服务于它的请求/响应类型、解析函数与测试桩一起清。成批包装留下的死代码没人维护，下游契约变更后响应结构漂移也不会暴露（FastAPI 曾出现 5 个批量统计方法把 Spring 的 `List/VO` 响应当 `Map` 返回值，直到 GoZero 侧同契约 bug 才被连带发现）。新增客户端方法前先确认调用方；确认手段：全仓检索方法名（Spring/GoZero 还要对照「接口 + 实现」两处），区分生产调用与 `*_test.go` / `*.spec.ts` / `src/test` 里的测试调用
   - **内部的「服务间接口」同样按调用方清理（四个服务统一要求）**：被内部令牌保护的接口若无人调用，先判断接口定位再处置——本该服务外部的对外化（去掉内部令牌），确无消费者的连实现一起删。识别方式、判定流程、连带清理范围、已清理清单与产物重生成（含 Spring `target/classes` 残留坑）见 `mix-workflow` 的「服务间内部接口与无效接口清理」一节
10. **HTTP 连接池必须随服务生命周期释放**，不能指望进程退出收尾。现状与要求：

- FastAPI 已规范：两个 `httpx.AsyncClient`（内网 `trust_env=False` 与外部抓取各一个）由 `lifespan` 创建、`yield` 之后 `aclose()`，**新增长连接客户端必须走同一处创建与释放**
- Spring 由容器管理 reactor-netty 全局连接池，无需手工关闭；但禁止在请求路径上反复 `WebClient.builder().build()`，应注入 `WebClient.Builder` 并缓存实例
- GoZero 已收口为单条链路：`ServiceDiscovery.Close()` → 三个业务 Client 的 `Close()` → `ClientContext.Close()` → `ServiceContext.Close()`，新增客户端必须接进来
- NestJS 已收口：`NacosService` 实现 `OnModuleDestroy`，注销 Nacos 实例 + `shutdown()` 熔断器 + `destroy()` 专用 agent；新增持有的连接资源挂同一处，不要另建包级 stop 函数

11. 服务发现基于 Nacos；新服务接入需注册实例并在 metadata 声明能力
    - **注册地址必须是网关容器能回连的本机 IP**：显式配置 `SERVER_IP`（Spring 为 `SERVER_ADDRESS`）时以它为准，未指定（空、`127.0.0.1`、`0.0.0.0`）则自动探测本机 IP；**禁止在 dev 模式下固定注册 `127.0.0.1`**。`./mix dev` 的网关跑在 Docker 里，容器内的 `127.0.0.1` 是容器自身，会让网关 `connect() failed (111: Connection refused)` 返回 502，且下游服务一条日志都没有（请求根本没到）
    - 同理，服务监听地址也不能只绑 `127.0.0.1`，dev 下的 `SERVER_IP` 应为 `0.0.0.0`，否则容器无论如何都连不上
12. 生成代码时参考目标服务同类文件的命名与组织方式；已有成熟风格优先
13. 注释说明：注释的结尾一律不带中文句号 `。`，直接留空；**散文式说明默认写成一行的单行注释**（IDE 悬停会把连续的行注释拼接成一段，一句话拆成多行等于没有换行），单行控制在 150 字符内；**内容结构化或一句话讲不完时才用多行**：多条并列、分步流程、参数或字段逐项说明、需要段落分隔或小节标题（如 `// ===== 缓存 TTL =====`）时分行书写，每行承载一条完整信息，只在语义边界处断行而不是按长度硬切；**把多行并成一行时必须用逗号、分号或冒号等标点衔接**，禁止用空格把两句话直接粘在一起（`// 启动读写处理，ctx 取请求上下文` 而不是 `// 启动读写处理 ctx 取请求上下文`）；`/** */` 块注释（Javadoc/JSDoc）不受此限制

- **单行注释结尾一律不带中文句号 `。`（四个服务统一，新增、修改与历史遗留的注释都按此清理）**：句末直接留空，改由换行、逗号、分号或冒号承担分隔
  - 纳入约束的注释形态：Spring / NestJS / GoZero 的 `// 单行说明` 与单行 `/** 单行说明 */`（Javadoc / JSDoc），FastAPI 的 `# 单行说明`、单行 `"""说明"""` 与多行 docstring 的最后一行
  - 多行注释只约束整体结尾那一行；中间行的句号是句子分隔，保留，删掉会让上下两句直接粘连
  - 不适用：字符串字面量、Prompt 模板、消息与提示文案，这类句号属于业务文本而不是注释
  - 交付前自查：`grep -rnE '(//|#|\*).*。\s*(\*/)?\s*$|。"""' spring gozero nestjs fastapi --include='*.java' --include='*.go' --include='*.ts' --include='*.py' --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=target --exclude-dir=__pycache__`，命中行末句号删除后重跑 `./mix format <service>`

14. **日志采集必须排除敏感字段**：请求体进入日志后会被投递到 `api-log-queue`，最终落在 MongoDB `apilogs` 与 ClickHouse `ods_api_log`，因此凡是携带密码、验证码、令牌、授权码的接口都要显式排除。各服务能力：Spring `@ApiLog(excludeFields = {...})`、NestJS `@ApiLog({ excludeFields: [...] })`、FastAPI `@logWithConfig(exclude_fields = [...])`（`@log` 不支持）；GoZero 通过可变参传入——`ApplyApiLog(rabbitPublisher, logger, handler, "操作描述", "password", "captcha")`，中间件内部用 `sanitizeBody` / `sanitizeQueryParams` 递归把命中字段（字段名大小写不敏感）替换为 `******`
    - **测试接口与内部令牌接口不投递 MQ**：`/test` 前缀的测试接口，以及用内部令牌保护的接口（Spring `@RequireInternalToken`、NestJS `@RequireInternalToken()`、FastAPI `@requireInternalToken`、GoZero 挂在 `InternalServiceMiddleware` 路由组上的 handler），一律只保留本地日志与耗时记录，不写入 `api-log-queue`，避免运维探活与服务间调用淹没接口日志
    - 开关写法：Spring `@ApiLog(value = "操作描述", skipMq = true)`、NestJS `@ApiLog({ message: "操作描述", skipMq: true })`、FastAPI `@log("操作描述", skip_mq=True)` 或 `logWithConfig(..., skip_mq=True)`、GoZero `ApplyApiLogSkipMq(rabbitPublisher, logger, handler, "操作描述")`；默认值均为「投递 MQ」，新增普通接口不需要显式声明
15. **新增接口必须带参数校验**，任何接收请求参数的接口都要声明校验规则，不得只靠业务层兜底。各服务写法见对应章节；**GoZero 的校验标签写在 `.api` 文件里**（随 goctl 生成进 `types.go`），漏写标签等于该参数没有校验，不会报错也不会告警
16. **新增、修改或删除对外接口后，必须重新生成静态 OpenAPI 文档并同步 Apifox**：先 `./mix swag <service>`，产物（`openapi.json` + `openapi.yaml`）与服务代码同一次提交；再 `./mix apifox <service>` 同步到 Apifox 并把更新后的 `.apifox/<service>.schemas.sha256` 一并提交，未配置令牌时跳过并说明。交付前用 `./mix swag-check <service>` 自校验产物与 Apifox 基线是否同步，CI 的 `docs-consistency` job 会拦截未同步的提交（`apifox-sync.yml` 在 prod 的同步只作兜底）。完整流程见 `mix-workflow` 的接口文档收尾流程
17. **业务配置统一经 YAML 导入环境变量**：服务配置值在对应 `application.yaml` 中声明 `${ENV_NAME:default}`，业务代码通过项目配置加载器或框架配置服务读取；禁止在业务模块直接调用 `os.getenv`、`process.env`、`System.getenv`、`os.LookupEnv` 等绕过 YAML。环境变量直接读取仅保留在配置加载器/启动引导，以及第三方库必须从标准进程环境读取且 YAML 无法替代的场景（如 HTTP 代理变量），新增例外需说明原因。可选变量当前不启用时，在 `.env`、`.env.example`、`.env.docker` 中注释变量行，并注明未配置时的默认行为；不要用空值赋值伪装成已配置
18. **接口响应必须使用具名结构，禁止匿名 Map**：控制器/路由的返回类型要有明确的结构定义并携带字段说明，便于 Swagger 呈现与下游解析。各服务落地：Spring 用 `entity/vo/` 下的 VO（字段加 `@Schema`）、NestJS 用 `common/utils/swaggerResponse.ts` 的 `SchemaObject` 加响应 DTO、FastAPI 用 `internal/schemas/` 的 Pydantic 模型、GoZero 用 `.api" 里的具名 `type`。**Spring 额外硬性要求**：禁止 `Map<String, Object>`（含 `java.util.Map`）作为控制器返回类型，`./mix lint spring`会检测；用于替换匿名 Map 的 VO 必须保持原有下划线字段名（类上加`@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)`），否则下游 FastAPI/GoZero 会解析不到字段；确实只能使用 Map 的场景（如列由运行时决定的动态查询结果）必须显式豁免：方法或其注解上方写 `// vo-exempt: 原因`，整个控制器写 `// vo-exempt-class: 原因`

19. **接口层只处理协议边界**：Controller、Handler、Router 负责参数绑定与校验、读取请求身份、调用面向用例的 Service/Logic、包装响应；可保留分页包装、简单 DTO/VO 转换、重定向和连接升级。关联查询、业务条件判断、多个业务服务的顺序编排、落库决策、缓存批量操作和异步任务执行放在应用服务、Logic 或任务组件。检查方法体内多个业务依赖调用、直接访问 Repository/Model/Cache、手工创建 DB 会话或自行维护聊天状态的情况
