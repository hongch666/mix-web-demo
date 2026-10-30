---
name: mix-web-demo
description: mix-web-demo 多语言微服务仓库专属编码规范，覆盖 Spring WebFlux、NestJS、FastAPI、GoZero 四个服务与 APISIX 网关的分层组织、依赖注入、请求校验、实时链路、日志、测试、常量、并行化、SQL 参数化、远程调用、Swagger 生成与 Apifox 同步约定，并含仓库工程约束（行尾、goctl 生成流程）与容器镜像约定（多阶段构建、镜像推送与版本、本地优先/远程兜底的镜像名前缀配置、各服务 .dockerignore 边界）。在本仓库生成或修改任何服务代码时必须使用；与通用 skills 冲突时以本 skill 的项目实证约定为准。
---

# mix-web-demo 项目专属编码规范

## 适用范围与配套 skills

本仓库包含四个业务服务与一个网关，生成代码前必须先确认目标服务：

| 目录       | 技术栈                                                   | 端口 |
| ---------- | -------------------------------------------------------- | ---- |
| `spring/`  | Spring Boot 3 WebFlux + R2DBC + WebClient + Resilience4j | 8081 |
| `gozero/`  | go-zero 1.10 + rest/httpc + validator + sqlx             | 8082 |
| `nestjs/`  | NestJS + Fastify + Mongoose/TypeORM + opossum            | 8083 |
| `fastapi/` | FastAPI + SQLAlchemy async + contextvars + APScheduler   | 8084 |
| `gateway/` | Apache APISIX（配置驱动，无业务代码）                    | 8080 |

配套通用 skills（本 skill 未覆盖的细节查阅它们，冲突时以本 skill 为准）：

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

## 按任务加载参考规范

- 创建、修改、删除或评审测试，以及修复需要回归测试的缺陷时，必须完整读取 [references/unit-testing.md](references/unit-testing.md)
- 测试规范只约束测试边界与质量，不要求为了覆盖率测试生成代码、DTO、getter 或第三方库内部行为

## 通用规则（全部服务）

1. 使用中文回复；代码注释与字符串信息使用中文；注释与说明不含任何 emoji 与标志
2. 不主动生成任何文档，除非明确要求
3. SQL 一律参数化，禁止字符串拼接用户值。各服务占位风格：Spring R2DBC 用 `:param`；FastAPI ClickHouse 用 `%(name)s`；GoZero sqlx 用 `?`；NestJS 走 ORM 方法 API
4. **每次生成或修改代码后必须执行代码格式化与格式检查**：先跑 `./mix format <service>` 自动格式化，再跑 `./mix lint <service>` 确认检查通过，不允许把未格式化的代码交付；省略服务名时处理 spring、gozero、nestjs、fastapi 全部，`gateway` 为配置驱动不参与
5. **交付前必须验证编译通过**：格式与 lint 之后跑 `./mix compile <service>`（只编译校验，不产出打包目录），未通过不得交付；该步骤与「验证命令」章节里各服务的编译命令等价，省略服务名时处理四个服务全部。`./mix compile` 与打包命令 `./mix dist build` 职责不同，不要用后者替代前者（后者会清理 dist 并产出可运行产物）。对应工具未安装时该服务返回码 2 自动跳过，不允许据此判定通过
   - **Windows 环境下所有 `./mix` 命令必须用 Git Bash 执行**，例如 PowerShell 中：`& "C:\Program Files\Git\bin\bash.exe" -c "./mix format spring"`。禁止用 PowerShell 直接 `./mix`（会被静默空跑，退出码 0 但什么都没做），也禁止用 WSL 的 `bash`（WSL 侧没有各服务工具链，会导致 gozero/fastapi 等被「工具未安装」跳过、NestJS 的 `tsc` 找不到 `node_modules/.bin` shim 而误报失败）。确认 Git Bash 安装路径不存在时改用本机服务工具链直接验证（如 `go build ./...`、`node node_modules/typescript/bin/tsc --noEmit`、`python -m compileall`），并如实说明未跑 mix
6. 常量抽取：四个服务均有常量类，消息类字符串必须进常量类引用
   - Spring：`common/constants/`（`Messages`、`Defaults`、`RedisKeys`、`Scripts`、`SqlTools`、`HttpCode`、`HeaderNames`、`MetricNames`、`RabbitQueues`、`SyncResource`、`SyncAction`、`SyncChangeType`、`TelemetryConstants`、`WarehouseResources`）
   - NestJS：`common/constants/`（`Messages`、`HttpCode`、`Defaults`、`ErrorIds`、`RedisKey`、`SqlTools`、`MongoTools`、`Swagger`、`Telemetry`、`MetricNames`、`ExportTemplate`）
   - FastAPI：`core/constants/`（`Messages`、`Defaults`、`HttpCode`、`ErrorCodes`、`RedisKeys`、`Scripts`、`WarehouseScripts`、`Prompts`、`Algorithm`、`Intent`、`Vector`、`AiUsers`、`SwaggerConfig`、`Telemetry`、`MetricNames`）
   - GoZero：`app/common/constants/`（`messages.go`、`defaults.go`、`validations.go`、`httpCode.go`、`remoteCall.go`、`redisKeys.go`、`scripts.go`、`sqlTools.go`）
   - 语言支持字符串模板时（Python f-string、TS 模板串、Go fmt），动态部分用模板拼接常量，不把整句抽离
   - **常量类内部成员顺序：函数型成员必须全部排在普通常量之前**（NestJS 为 `static readonly NAME = (...) => ...` 形式的静态属性，FastAPI 为 `@staticmethod` 方法），新增常量时先写函数成员再写普通常量；该约定由 `./mix lint` 里的 `scripts/constants.py` 检查并报错，`./mix format` 不做任何常量整理（Spring 与 GoZero 的常量前缀与其配套方法成对书写，只检查注释与分类，不参与顺序检查）
   - **常量注释与分类（四个服务统一）**：每个常量与每个函数型成员都必须带能被 IDE 悬停展示的注释，注释写在成员的声明处而不是集中写一块
     - Spring：成员上方 `/** 单行说明 */`（Javadoc），字段用单行形式，不需要 `@param` 之类的标签
     - NestJS：成员上方 `/** 单行说明 */`（JSDoc），与类、方法的 JSDoc 同一风格
     - GoZero：成员上方 `// 单行说明`，逐行注释，与 gofmt 对齐后的列宽无关
     - FastAPI：普通常量写在**变量下方**的三双引号字符串里（PEP 257 属性文档串，Pylance 与 PyCharm 会作为悬停说明展示），形如 `ARTICLE_TOP10: str = "article:top10"` 下一行写 `"""文章阅读量前十榜单的缓存 key"""`；`@staticmethod` 方法仍写在函数体内第一行
     - 成员按用途分类摆放，每个分类以单行分类注释开头：Java / NestJS / GoZero 用 `// ===== 分类名 =====`，FastAPI 用 `# ===== 分类名 =====`；分类注释与下方的成员注释之间空一行，分类内部不再拆散不相干的常量，Go 的 `const` / `var` 块把分类注释写在 `const (` 上方或块内首行均可
     - 注释内容说明该常量的用途、取值来源或与其它服务的对齐关系（如「需与 GoZero 侧 `SEARCH_GRAPH_CANDIDATE_LIMIT` 保持一致」），不复述常量名与字面值；结尾不加中文句号（见通用规则 13）
     - 该约定由 `./mix lint` 里的 `scripts/constants.py` 检查：缺少成员注释、成员未归入任何分类都会报错并打印文件与行号
   - 注解 / 装饰器的字符串参数**不抽常量**，直接写字面量：这类字符串只在声明处使用一次，抽到常量类后需跳转查看，反而降低可读性
     - Spring：`@Operation(summary, description)`、`@Tag`
     - NestJS：`@ApiOperation({ summary, description })`、`@ApiTags`
     - FastAPI：`@router.get/post(..., summary=, description=)`
     - GoZero 无注解机制，不适用本条
7. 相互独立的 IO 调用（RPC/HTTP/DB/Redis/ES/MQ）必须并行化，禁止串行等待；各服务并行原语见对应章节
8. 日志遵循各服务现有封装（见各服务章节），禁止绕过封装直接 print/console/logx 散用
9. 远程调用统一走各服务封装的客户端，自动透传用户上下文头：`X-User-Id`、`X-Username`、`X-Session-Id`、`Authorization`、`X-Internal-Token`；无登录用户时内部令牌 `userId=-1` 表示系统调用。禁止在新代码里裸用 httpx/axios/WebClient/http.Client 直连其他服务。各服务的唯一入口与底层 HTTP 客户端：
   - Spring：`infra/client/ServiceWebClient`（**WebClient** + `@LoadBalanced` 按服务名寻址 + Resilience4j 熔断/重试），按目标服务加方法
   - GoZero：`app/common/client` 的 `ServiceDiscovery.CallService`（**go-zero `rest/httpc`** + Nacos 轮询 + 退避重试），按目标服务在 `internal/client/` 封装
   - NestJS：`module/common/nacos/nacos.service.ts` 的 `call(opts)`（**axios** + axios-retry + opossum），按目标服务在调用方封装 Client 类
   - FastAPI：`app/core/client/client.py` 的 `call_remote_service`（**httpx** 共享连接池 + SimpleCircuitBreaker + tenacity），按服务在 `internal/clients/` 封装
   - **客户端只保留有生产调用方的方法（四个服务统一要求）**：不要照下游接口清单成批包装；只为单测存在或完全无引用的方法直接删掉，连同只服务于它的请求/响应类型、解析函数与测试桩一起清。成批包装留下的死代码没人维护，下游契约变更后响应结构漂移也不会暴露（FastAPI 曾出现 5 个批量统计方法把 Spring 的 `List/VO` 响应当 `Map` 返回值，直到 GoZero 侧同契约 bug 才被连带发现）。新增客户端方法前先确认调用方；确认手段：全仓检索方法名（Spring/GoZero 还要对照「接口 + 实现」两处），区分生产调用与 `*_test.go` / `*.spec.ts` / `src/test` 里的测试调用
   - **内部的「服务间接口」同样按调用方清理（四个服务统一要求）**：被内部令牌保护的接口若无人调用，先判断接口定位再处置——本该服务外部的对外化（去掉内部令牌），确无消费者的连实现一起删。识别方式、判定流程、连带清理范围、已清理清单与产物重生成（含 Spring `target/classes` 残留坑）见「服务间内部接口与无效接口清理」一节
10. **HTTP 连接池必须随服务生命周期释放**，不能指望进程退出收尾。现状与要求：

- FastAPI 已规范：两个 `httpx.AsyncClient`（内网 `trust_env=False` 与外部抓取各一个）由 `lifespan` 创建、`yield` 之后 `aclose()`，**新增长连接客户端必须走同一处创建与释放**
- Spring 由容器管理 reactor-netty 全局连接池，无需手工关闭；但禁止在请求路径上反复 `WebClient.builder().build()`，应注入 `WebClient.Builder` 并缓存实例
- GoZero 已收口为单条链路：`ServiceDiscovery.Close()` → 三个业务 Client 的 `Close()` → `ClientContext.Close()` → `ServiceContext.Close()`，新增客户端必须接进来
- NestJS 已收口：`NacosService` 实现 `OnModuleDestroy`，注销 Nacos 实例 + `shutdown()` 熔断器 + `destroy()` 专用 agent；新增持有的连接资源挂同一处，不要另建包级 stop 函数

11. 服务发现基于 Nacos；新服务接入需注册实例并在 metadata 声明能力
    - **注册地址必须是网关容器能回连的本机 IP**：显式配置 `SERVER_IP`（Spring 为 `SERVER_ADDRESS`）时以它为准，未指定（空、`127.0.0.1`、`0.0.0.0`）则自动探测本机 IP；**禁止在 dev 模式下固定注册 `127.0.0.1`**。`./mix dev` 的网关跑在 Docker 里，容器内的 `127.0.0.1` 是容器自身，会让网关 `connect() failed (111: Connection refused)` 返回 502，且下游服务一条日志都没有（请求根本没到）
    - 同理，服务监听地址也不能只绑 `127.0.0.1`，dev 下的 `SERVER_IP` 应为 `0.0.0.0`，否则容器无论如何都连不上
12. 生成代码时参考目标服务同类文件的命名与组织方式；已有成熟风格优先
13. 注释说明：注释的结束不能包含中文句号，直接留空；**散文式说明默认写成一行的单行注释**（IDE 悬停会把连续的行注释拼接成一段，一句话拆成多行等于没有换行），单行控制在 150 字符内；**内容结构化或一句话讲不完时才用多行**：多条并列、分步流程、参数或字段逐项说明、需要段落分隔或小节标题（如 `// ===== 缓存 TTL =====`）时分行书写，每行承载一条完整信息，只在语义边界处断行而不是按长度硬切；**把多行并成一行时必须用逗号、分号或冒号等标点衔接**，禁止用空格把两句话直接粘在一起（`// 启动读写处理，ctx 取请求上下文` 而不是 `// 启动读写处理 ctx 取请求上下文`）；`/** */` 块注释（Javadoc/JSDoc）不受此限制

- 新增或修改的代码注释、装饰器说明和文档说明均不得以中文句号 `。` 结尾，统一以无句号文本或其他必要标点结束

14. **日志采集必须排除敏感字段**：请求体进入日志后会被投递到 `api-log-queue`，最终落在 MongoDB `apilogs` 与 ClickHouse `ods_api_log`，因此凡是携带密码、验证码、令牌、授权码的接口都要显式排除。各服务能力：Spring `@ApiLog(excludeFields = {...})`、NestJS `@ApiLog({ excludeFields: [...] })`、FastAPI `@logWithConfig(exclude_fields = [...])`（`@log` 不支持）；GoZero 通过可变参传入——`ApplyApiLog(rabbitPublisher, logger, handler, "操作描述", "password", "captcha")`，中间件内部用 `sanitizeBody` / `sanitizeQueryParams` 递归把命中字段（字段名大小写不敏感）替换为 `******`
15. **新增接口必须带参数校验**，任何接收请求参数的接口都要声明校验规则，不得只靠业务层兜底。各服务写法见对应章节；**GoZero 的校验标签写在 `.api` 文件里**（随 goctl 生成进 `types.go`），漏写标签等于该参数没有校验，不会报错也不会告警
16. **新增、修改或删除对外接口后，必须重新生成静态 OpenAPI 文档并同步 Apifox**：先 `./mix swag <service>`，产物（`openapi.json` + `openapi.yaml`）与服务代码同一次提交；再 `./mix apifox <service>` 同步到 Apifox，未配置令牌时跳过并说明。完整流程见「接口文档收尾流程」章节
17. **业务配置统一经 YAML 导入环境变量**：服务配置值在对应 `application.yaml` 中声明 `${ENV_NAME:default}`，业务代码通过项目配置加载器或框架配置服务读取；禁止在业务模块直接调用 `os.getenv`、`process.env`、`System.getenv`、`os.LookupEnv` 等绕过 YAML。环境变量直接读取仅保留在配置加载器/启动引导，以及第三方库必须从标准进程环境读取且 YAML 无法替代的场景（如 HTTP 代理变量），新增例外需说明原因。可选变量当前不启用时，在 `.env`、`.env.example`、`.env.docker` 中注释变量行，并注明未配置时的默认行为；不要用空值赋值伪装成已配置
18. **接口响应必须使用具名结构，禁止匿名 Map**：控制器/路由的返回类型要有明确的结构定义并携带字段说明，便于 Swagger 呈现与下游解析。各服务落地：Spring 用 `entity/vo/` 下的 VO（字段加 `@Schema`）、NestJS 用 `common/utils/swaggerResponse.ts` 的 `SchemaObject` 加响应 DTO、FastAPI 用 `internal/schemas/` 的 Pydantic 模型、GoZero 用 `.api" 里的具名 `type`。**Spring 额外硬性要求**：禁止 `Map<String, Object>`（含 `java.util.Map`）作为控制器返回类型，`./mix lint spring`会检测；用于替换匿名 Map 的 VO 必须保持原有下划线字段名（类上加`@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)`），否则下游 FastAPI/GoZero 会解析不到字段；确实只能使用 Map 的场景（如列由运行时决定的动态查询结果）必须显式豁免：方法或其注解上方写 `// vo-exempt: 原因`，整个控制器写 `// vo-exempt-class: 原因`

19. **接口层只处理协议边界**：Controller、Handler、Router 负责参数绑定与校验、读取请求身份、调用面向用例的 Service/Logic、包装响应；可保留分页包装、简单 DTO/VO 转换、重定向和连接升级。关联查询、业务条件判断、多个业务服务的顺序编排、落库决策、缓存批量操作和异步任务执行放在应用服务、Logic 或任务组件。检查方法体内多个业务依赖调用、直接访问 Repository/Model/Cache、手工创建 DB 会话或自行维护聊天状态的情况

## Spring 服务（spring/，WebFlux 响应式栈）

### 目录组织（入口、应用、基础设施与横切）

```
web/controller   HTTP 接口层（返回 Mono/Flux）
web/filter|exception  请求过滤与异常映射
web/security/annotation|aspect  权限注解与切面
web/logging/annotation|aspect  接口日志注解与切面
web/sync/annotation|aspect  变更同步注解与切面
application/service      业务接口
application/service/impl 业务实现
application/task  定时调度
infra/repository R2DBC Repository
entity/po|vo|dto|event|projection  实体、视图对象、领域事件与投影（跨服务变更事件放 entity/event）
entity/assembler 实体到 VO 的装配器（依赖 infra/repository，供 service/impl 复用，跨包调用需 public）
infra/client     远程调用客户端（ServiceWebClient）
bootstrap       启动环境与初始化（Starter、DotenvInitializer、InitMessageInitializer、DatabaseInitializer）
config|config/properties  Bean 配置与配置属性
observability   指标记录（MetricsRecorder）
common/constants|utils  常量与工具（RedisUtil、JwtUtil、UserContext）
```

测试文件按被测类的包路径放在 `spring/src/test/java/com/hcsy/spring/` 下，例如 `web/logging/aspect/ApiLogAspectTest.java`、`web/security/aspect/RequirePermissionAspectTest.java` 与 `application/service/impl/ArticleServiceImplTest.java`

### 硬性约定

- **控制器返回类型禁止匿名 Map**：一律用 `entity/vo/` 下的 VO 并给字段加 `@Schema`，`./mix lint spring` 会检查（`scripts/controller-vo.py`）。把原先的 `Map<String, Object>` 换成 VO 时，类上必须加 `@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)` 保持 `user_id`、`create_time` 这类下划线字段名，否则 FastAPI/GoZero 按原字段名解析会取不到值；只有运行时结构不固定（动态列、动态键）时才允许 Map，并在方法或其注解上方写 `// vo-exempt: 原因`，整类场景写 `// vo-exempt-class: 原因`
- **依赖方向**：`web` 调用 `application/service`，应用服务使用 `infra` 的客户端与 Repository；`application/task` 调用业务服务，`web/sync` 的切面调用同步服务。`common` 不依赖 `web` 或 `application`；`entity/assembler` 现有实现依赖 `infra/repository`，新增跨层组件前先确认依赖方向
- 文章创建/更新的作者解析、评论创建/更新的关联规则与评论列表补全由应用服务执行；Controller 只映射原接口的成功或缺失响应。定时任务的异步订阅由任务组件启动，Controller 只触发任务。保留 `@ArticleSync` / `@DataSync` 所需的创建主键与成功结果形态
- ORM 是 Spring Data R2DBC，不是 MyBatisPlus：Repository 继承 `ReactiveCrudRepository<T, ID>`；自定义 SQL 用 `@Query` + `:param`，更新加 `@Modifying`；事务用 `TransactionalOperator.transactional()` 包裹，禁止 `@Transactional`
- **跨实体的动态 Criteria 查询不建 Repository 类**：`infra/repository` 里只放继承 `ReactiveCrudRepository` 的接口；需要 `R2dbcEntityTemplate` + `Criteria`/`Query` 动态拼条件时（参照 `CommentsServiceImpl`、`WarehouseSyncServiceImpl`），注入模板后写成对应 `service/impl` 的私有成员方法，不要新造泛型 `XxxRepository` 类或 `XxxQuerySupport`。实体属性名、排序字段这类只能运行时验证的字符串，在 `@PostConstruct` 里做启动期校验（例如数仓水位线属性），让写错时启动即失败而不是首次查询才报错
- Controller 返回 `Mono<Result<T>>` / `Flux<Result<T>>`，Service 返回 `Mono<T>` / `Flux<T>`；禁止返回裸类型、禁止调用 `.block()`
- 请求上下文走 Reactor Context：`UserContextWebFilter` 用 `.contextWrite()` 写入，业务用 `Mono.deferContextual(ctx -> ...)` 读取 `UserContext.getUserId(ctx)`；禁止 `ThreadLocal`、`RequestContextHolder`、`OncePerRequestFilter`、`HandlerInterceptor`
- 并行独立 IO 用 `Mono.zip()` / `Mono.when()`，禁止 `CompletableFuture.allOf()`
- 阻塞操作（加密、验证码图片等）用 `Mono.fromCallable(() -> ...).subscribeOn(Schedulers.boundedElastic())` 隔离
- 全局异常：`@RestControllerAdvice` + `@ExceptionHandler` 返回 `Mono<ResponseEntity<Result<?>>>`，通过 ResponseEntity 设置 HTTP 状态码；`ResponseBodyAdvice` 在 WebFlux 不可用
- **WebFlux 的请求体校验失败抛的是 `WebExchangeBindException`（继承 `ServerWebInputException`），不是 MVC 的 `MethodArgumentNotValidException` / `org.springframework.validation.BindException`**。`@ExceptionHandler` 未声明它就会被 `@ExceptionHandler(Exception.class)` 兜底吞成 500，必须显式声明；畸形 JSON 与参数类型不匹配抛 `ServerWebInputException`，一并声明。字段消息取 `getBindingResult().getFieldError().getDefaultMessage()`
- **请求 DTO 用 jakarta 注解声明约束（放 `entity/dto/`），控制器参数用 `@Valid` 触发**；新增接口必须带校验（通用规则 13），只有 `@RequestParam` / `@PathVariable` 这类无 DTO 的入参属于例外，那种情况控制器**没有**类级 `@Validated`，需要在 service 层手工校验
- 微服务调用用 `ServiceWebClient`（WebClient + `@LoadBalanced` 服务名寻址 + Resilience4j 熔断/重试），新增远程接口在该类中加方法，通过 `deferContextual` 注入上下文头；禁止 OpenFeign。**WebClient 在构造时构建一次并缓存为 final 字段复用**（WebClient 不可变且线程安全），不要在请求路径上反复 `build()`
- Redis 用 `ReactiveStringRedisTemplate`，封装在 `common/utils/RedisUtil`；缓存读写走 Mono 链式 `switchIfEmpty(Mono.defer(...))` 模式，禁止 `@Cacheable`
- AOP 切面中 `pjp.proceed()` 返回 `Mono<?>` 时必须在 Mono 链内操作（`.flatMap()` / `.doOnSuccess()`），上下文用 `.deferContextual()` 获取
- 横切能力由 AOP 实现：`ApiLogAspect`（接口日志）、`RequirePermissionAspect`（`@RequirePermission` 声明式权限）、`RequireInternalTokenAspect`（`@RequireInternalToken` 内部令牌）、`ArticleSyncAspect`（文章变更同步 MQ / ES / 向量）、`DataSyncAspect`（图谱与数仓同步）。切面类与注解同名（注解去 `@` 加 `Aspect` 后缀），新增切面沿用该命名。新增写接口时确认是否需要权限注解与同步触发，同步失败只记日志、没有补偿机制
- **响应式切面的固定写法**：`pjp.proceed()` 返回的是**未订阅的冷流**（业务代码此时尚未执行），且 Reactor Context 只在订阅时可见。所以切面必须把校验 / 日志 / 同步挂到 Mono 链上（`Mono.deferContextual(ctx -> ...)`）：校验类用 `validate(ctx).then(businessMono)` 保证「校验先于业务」，副作用类用 `monoResult.doOnSuccess(...)` 发后即忘；副作用里若需要用户身份，必须用 `UserContext.writeContext(Context.empty(), ...)` 重建 Context 再 `contextWrite`，否则异步链上读不到。**禁止用同步代码在 `proceed()` 之前读上下文**，那时 ctx 不可见，只会拿到 null
- 注入风格：`@Service` + `@RequiredArgsConstructor` + `private final` 字段（构造器注入），禁止字段 `@Autowired`
- 外部基础设施统一由 Spring Bean 提供：`PasswordEncryptor` 注入 `BCryptPasswordEncoder`，禁止在工具或 Service 内部直接 `new` 加密器、客户端或连接资源；新增同类依赖放入 `config` 的 `@Configuration` Bean
- Swagger 用 springdoc：`@Operation(summary, description)`、`@Tag`，注解参数直接写字面量，不抽常量
- 日志：`common/utils/SimpleLogger` 实例注入使用
- **配置项一律声明为 `config/properties/` 下的 `@ConfigurationProperties` record，读取配置只能通过注入这些类，禁止 `@Value` 字段**（main 侧当前已无 `@Value`：`logging.include-timestamp` / `logging.file.path` 由 `LoggingProperties` / `LoggingFileProperties` 承接，`server.mode` / `server.port` 由 `ServerProperties` 承接，`SimpleLogger`、`InitMessageInitializer`、`SwaggerConfig` 均走构造器注入）；配置元数据由 `spring-boot-configuration-processor` 自动生成：类 Javadoc 用 `@param` 写描述（续行不能以 `@` 开头，否则描述会被截断），原始类型组件的默认值必须用 `@DefaultValue` 显式声明（不写会落成 `0` / `false`，与 YAML 的 `${ENV:default}` 漂移），`@ConfigurationPropertiesScan` 负责注册；`META-INF/additional-spring-configuration-metadata.json` 当前不存在，只有确实无法建模的键才新建，补了绑定类后必须同步删掉手写条目；`server` 这类 Boot 自带前缀也能建绑定类，与 Boot 自身的 `ServerProperties` 同前缀共存时双方各绑各的字段、未知键忽略，但自定义配置优先用独立前缀；离线文档切片测试 `OpenApiDocGenerator` 不加载 `@ConfigurationPropertiesScan`，给被 `@Import` 的配置类新增配置依赖时要在 `MockConfiguration` 里补对应 Bean；新增或修改配置键后跑 `./mix compile spring` 并核对 `target/classes/META-INF/spring-configuration-metadata.json` 的 `description` 与 `defaultValue`
- **类（含接口、抽象类、枚举、记录、注解类型）与方法（含构造器）必须带 Javadoc 注释**（风格参考 `infra/client/ServiceRequestOptions.java` 的三行 `/** 微服务请求的可选参数 */`）：类/接口/注解类型说明职责，方法说明做什么及关键语义（响应式语义与下游用途可提及）；单句简体中文、结尾不加中文句号；带注解的声明注释写在首个注解上方；`src/test` 不要求，已存在的注释不改写。新增声明遗漏注释视同未完成

## NestJS 服务（nestjs/，Fastify + Mongoose/TypeORM）

### 目录组织

```
config/           YAML 配置与 index.ts 加载器
common/constants  常量（Messages、HttpCode、Defaults、ErrorIds）
common/exceptions 全局异常与错误结构
common/utils      工具类（response、swaggerResponse 响应 Schema、snakeCase 命名转换原语）
framework/        全局横切：decorators、guards、interceptors、filters、middleware
module/common/    公共服务模块（nacos、logger、oss、redis、mail、github、client）
module/system/    系统业务模块（apiLog、articleLog、sqlTools、task 等）
```

### 模块内组织与约定

- 每个业务模块：`xxx.module.ts` + `xxx.controller.ts` + `xxx.service.ts`，辅以 `dto/` 与 `schema/`（Mongoose）或 `entities/`（TypeORM）
- ORM 按模块现状选择：日志类用 Mongoose（`@Schema` + `SchemaFactory`，`@InjectModel`）；结构化表用 TypeORM（`@InjectRepository`）。新模块先参考同类模块，禁止凭空引入新 ORM
- **入参校验走全局 `ValidationPipe`（`app/index.ts` 注册，`transform` + `enableImplicitConversion`），DTO 用 class-validator 注解**；新增接口必须带校验（通用规则 13），每个 `@Body()` / `@Query()` / `@Param()` 都要有对应 DTO 与约束注解，直接用裸参数接请求等于没有校验。自定义 `exceptionFactory` 把错误包成 `BusinessException(400, PARAM_PARSE_FAILED)`，最终由 `AllExceptionsFilter` 输出统一结构。**当前未开 `whitelist` / `forbidNonWhitelisted`**，未声明字段既不剥离也不报错，不要依赖"多余字段会被拒"
- 请求上下文用 nestjs-cls：`ClsMiddleware` 写入（userId/username/sessionId/token/internalToken），业务注入 `ClsService` 读取；gRPC 或脱离 HTTP 异步链的场景必须用 `ClsService.run` 手动开启上下文
  - **未登录语义注意**：`parseUserId` 要求 `Number.isInteger(userId) && userId > 0`，所以 ≤0 的值（含约定的系统调用 `-1`）在 CLS 里是 `undefined`；出站头由 `NacosService.call` 生成（`X-User-Id: String(userId || 0)`，内部令牌按 `userId > 0 ? userId : -1`）。需要区分"未登录 / 系统调用"时不要直接依赖 CLS 的值
- 公共层入口是 `module/common/common.module.ts`：`imports` 只保留需要根级加载的子模块（Logger、Client、Github、Mail），`exports` **只导出 ClientModule**（根模块的 `RequireAdminGuard` 需要它）。业务模块用到的其他公共能力（oss、word、nacos、redis）由消费方**自行 import 对应模块**，禁止把 CommonModule 做成"全量中转池"（那会让模块边界形同虚设）；定时任务（TaskModule）属系统业务，放 `module/system/task`，不进 CommonModule，避免 common 层反向依赖 system 层
- 外部客户端必须通过模块 Provider 注入：Mail 的 Nodemailer Transporter 使用 `MAIL_TRANSPORTER` Provider，OSS 的 ali-oss 客户端使用 `OSS_CLIENT` Provider；Service 构造函数只接收抽象依赖，禁止直接调用 `nodemailer.createTransport()` 或 `new ali-oss(...)`
- `LoggerModule` 是 `@Global`，日志能力全模块可直接注入，无需 import
- 用户可控字符串在拼接存储 key 前必须清洗（长度 + 字符白名单）：`upload` 模块的 `customFilename` 走 `@Query` 原样拼 OSS key，属需要加固的写法
- 远程调用统一走 `module/common/nacos/nacos.service.ts` 的 `call(opts: CallOptions)`（Nacos 发现 + 轮询 + opossum 熔断 + axios-retry + 自动上下文头/内部令牌），按目标服务在调用方封装 Client 类。**`NacosService` 自持专用 `http`/`https` Agent（keepAlive）并传给每次 `axios.request`**，不再依赖 `http.globalAgent`；`onModuleDestroy` 负责注销 Nacos 实例、`shutdown()` 全部熔断器、`destroy()` 两个 agent。新增远程调用必须复用同一个 agent，不要在模块里另建 axios 实例。两个坑：**`NacosNamingClient._close()` 不可用**（私有方法且内部调用的是不存在的 `this._beatReactor.close()`，beat_reactor 只定义了 `_close`，调用会抛错），所以只做 `deregisterInstance`；**`src/types/nacos.d.ts` 是项目自建的类型声明**，用到新的 SDK 方法要在这里补声明，否则编译不过
- 独立异步调用用 `Promise.all` 并行；条件不满足时用 `Promise.resolve(空值)` 占位保证数组结构一致
- 并行调用中存在「部分失败可容忍」时用 `Promise.allSettled`，逐项判断 `status` 决定降级或抛出，避免单个失败拖垮整体；不要用 `Promise.all` + `catch` 吞异常来模拟降级，会丢失失败项与输入项的对应关系
  - 批量任务逐项降级（参考 `module/system/sqlTools/sqlTools.service.ts` 并行查多表行数）：`results.map((r, i) => r.status === "fulfilled" ? r.value : 降级值)`，用索引 `i` 关联回输入项
  - 多个独立调用中区分必选与可选（参考 `module/common/github/github.service.ts` 并行拉 profile 与 email）：解构后分别判断，必选项 `rejected` 直接 `throw reason`，可选项 `fulfilled` 才取值、否则走兜底
- 尽可能使用 TypeScript 类型标注（接口、泛型、联合类型），即使编译通过也补全类型
- 遵循项目 `eslint.config.mjs`，提交前通过 lint
- Swagger 用 `@nestjs/swagger`：`@ApiOperation({ summary, description })`、`@ApiTags`，注解参数直接写字面量，不抽常量
- **响应模型必须显式声明**：TypeScript 泛型会在运行时擦除，不能只依赖 `Promise<ApiResponse<T>>` 生成 Swagger schema。对统一响应使用 `common/utils/swaggerResponse.ts` 的 `ApiResponseModel`，为 `data` 传入具体的 `SchemaObject`；空响应使用 `SwaggerNullData`，字符串、数组和对象响应分别声明对应结构。OAuth 重定向等非 JSON 响应使用 `ApiRedirectResponse`，不要套统一响应包装体
- **内联响应会在文档构建阶段提升为具名模型**：`app/swagger.ts` 的 `hoistInlineSchemas` 把每个接口的内联请求体与响应搬进 `components.schemas`，命名 `<Nestjs><路径><方法>[状态码]Response/Request`，因此 Apifox 里每个接口都有独立可复用的数据模型；`text/event-stream` 事件流响应与 `multipart/form-data` 请求体保持内联（Apifox 靠内联帧的 `title` 渲染流式响应、按原生方式处理文件字段）
- **响应 Schema 必须统一抽离**：业务响应的 `SchemaObject`（包括分页、同步、统计、上传和查询结果）统一定义在 `common/utils/swaggerResponse.ts`，控制器中的 `@ApiResponseModel` 只引用命名常量，禁止在控制器内重复编写内联 `data: { ... }`。除 `data: null` 外，必须为实际字段、数组项和嵌套对象补充 `description`；不能用无字段的 `SwaggerObjectData` 代替已知结构。
- **路径和查询参数命名必须与实际 URL 一致**：本项目 OpenAPI 会将字段转换为 snake_case。路径参数统一使用 snake_case，并让路由、`@Param`、`@ApiParam` 三处名称完全一致，例如 `:user_id` + `@Param("user_id")`、`:table_key` + `@Param("table_key")`。查询参数也必须统一，例如 `custom_filename` + `@Query("custom_filename")`，禁止同时出现 camelCase 与 snake_case。
- **Swagger 参数重复检查**：修改接口后重新生成 OpenAPI，检查每个 operation 的 `parameters` 是否存在重复语义或同时存在大小写不同的参数；重点排查 `userId/user_id`、`tableKey/table_key`、`customFilename/custom_filename` 等组合。
- **对外字段命名转换只在 `common/utils/snakeCase.ts` 一处维护**：请求 DTO 用 `@ExposeName()` 把驼峰属性声明为下划线键名（依赖全局 `ValidationPipe` 的 `transform`），响应由 `framework/interceptors/fieldNaming.interceptor.ts` 全局递归转换，Swagger 文档由 `common/utils/swaggerSnakeCase.ts` 的 `applySwaggerSnakeCase` 转换，三者共用同一个 `toSnakeCase`。新增或调整命名规则一律改该文件，禁止在拦截器、DTO 或 Swagger 后处理里另写正则——三处规则漂移会让文档、请求、响应对不上，且没有任何机制会告警。已知边界：连续大写字母会被逐个拆分（`myAPIKey` → `my_a_p_i_key`）；拦截器对 `content` 键的值不做递归转换（业务数据内部键由写入方决定，避免 MongoDB 驼峰与数仓下划线落成两套键名）
- 日志：注入 `LoggerService`（`module/common/logger`）
- **类、接口、函数与方法必须带 JSDoc 注释**（风格参考 `common/utils/batchBuffer.ts` 的三行 `/** 攒批配置选项 */`）：Service/Controller/Module/DTO/接口说明职责，方法说明做什么及关键语义；单句简体中文、结尾不加中文句号；带装饰器的声明注释写在首个装饰器上方；`*.spec.ts` 不要求，已存在的注释不改写。新增声明遗漏注释视同未完成

## FastAPI 服务（fastapi/）

聊天路由只保留请求绑定与 `StreamingResponse`：模型选择、用户身份兜底、LangSmith 生命周期、聊天历史保存、流式累计状态和 SSE 帧格式转换归 `ChatApplicationService`，路由直接调用该服务的 `stream_frames`。流式格式测试与聊天用例测试统一放在 `tests/internal/services/chat/chatApplicationService_test.py`。模型失败以异常或明确状态传递，不能通过回复文本是否含“错误”“失败”等词判断。手动任务路由只登记后台任务，同步模式选择归 `tasks/logic/`；缓存清理清单与并发执行由注入的分析 Service 负责，导出并上传等连续业务步骤也由 Service 封装

### 目录组织

```
app/core/         基础设施：auth、base(Logger)、client(远程调用)、config、constants、db、errors、decorators、middleware（contextvars 上下文中间件）
app/internal/api        路由（按业务分 router）
app/internal/services   业务服务（类组织 + 工厂函数）
app/internal/crud       数据访问 Mapper（含 ClickHouse 查询）
app/internal/models     SQLAlchemy 模型
app/internal/schemas    Pydantic 模型
app/internal/clients    按服务封装的远程客户端（SpringClient、NestjsClient、GozeroClient）
app/internal/cache      两级缓存（L1 内存 + L2 Redis + 版本号失效）
app/internal/tasks      APScheduler 调度任务（scheduler.py + logic/）
app/internal/agents     LangChain Agent 与工具
```

### 硬性约定

- 依赖注入分三层，各有固定登记处：
  - 定义层 `internal/{clients,crud,cache}/` 各文件底部：类 + 构造 + `@lru_cache` 工厂三位一体
  - 注册层 `app/dependencies/` 包（`database.py`、`mappers.py`、`caches.py`、`clients.py`、`services.py`、`tools.py`、`llm.py`）：集中定义 `Annotated` 别名（`DbSession`、`XxxServiceDep`、`XxxToolDep`），由包 `__init__.py` 统一导出
  - 装配层 `dependencies/services.py` / `tools.py` / `llm.py`：`provide_xxx(...)` 函数，**参数即依赖别名**，函数体调用底层工厂；服务与工具的构造依赖必须由这里显式传入，构造函数内不得自建依赖
- 注册范围只含**路由函数签名里直接出现**的依赖（DB 会话 + 服务 + agent 工具）；Client / Mapper / Cache 工厂不注册，只被 `provide_*` 与 `get_*_service` 消费
- `@lru_cache` 工厂是承重墙：`provide_*` 每次请求都会执行，底层工厂漏 `@lru_cache` 会让 `get_xxx_service` 的缓存按新键无界累积
- 非请求链路（APScheduler 任务）用 `resolve_xxx_service()` 复用同一组单例工厂，禁止 `cls(...)` 直接 new（会造出第二个实例、内部状态不共享）
- 全异步：接口必须 `async def`；优先用 asyncio 生态；同步阻塞库（clickhouse_driver、连接池同步接口）用 `asyncio.to_thread(...)` 包裹后 `await`
- 并行：独立 IO 用 `asyncio.gather`；循环内并行把每次迭代封装为内部 async 函数后 gather
- `__init__.py` 导出：包内有 `__init__.py` 导出的功能，导入一律走包路径（`from app.internal.crud import UserAnalysisMapper`），禁止深入到文件路径；新增模块必须同步更新 `__init__.py` 导出。该约定由 `./mix lint` 里的 `scripts/package-imports.py` 检查（目标目录没有 `__init__.py`、与目标同包、或导入方位于目标包导入链上时不受约束），历史违规可执行 `python scripts/package-imports.py --fix fastapi` 批量整理
- `internal/services` 每个业务子目录及 `llm/extend` 都在自身 `__init__.py` 导出公开类和工厂；顶层 `services/__init__.py` 只从子包聚合导出，避免跨层直接指向具体服务文件。新增业务服务时同步维护子包与顶层两级导出
- 类型标注全覆盖；`import` 全部在文件顶部，禁止逻辑中导入；生成后检查并删除未使用的 import
- **入参校验用 Pydantic 模型**（放 `internal/schemas/`，文件名 `xxxDTO.py`）：字段用 `Field(...)` 声明，单字段规则用 `@field_validator` + `PydanticCustomError`（中文消息，参考 `createHistoryDTO.py`），请求体禁止用裸 `dict` / `Any` 接收；新增接口必须带校验（通用规则 13）
- **统一响应模型使用泛型**：`core/base/response.py` 的 `ApiResponse[T]` 负责声明 `code`、`msg` 和 `data`，路由必须通过 `response_model=ApiResponse[具体类型]` 暴露返回结构。已知结构使用领域 DTO、列表或字典泛型；只有运行时结构确实不固定时才使用 `ApiResponse[object]`，禁止退回不带类型参数的 `ApiResponse`
- **FastAPI 响应结构必须可展开**：已知返回字段必须定义 Pydantic 响应 DTO，并在路由使用 `response_model=ApiResponse[具体 DTO]`；禁止用 `ApiResponse[object]` 隐藏可确定的 `data` 结构。DTO 的每个字段、嵌套对象和列表项都要用 `Field(description=...)` 写明含义。
- **DTO 字段内部驼峰、对外蛇形，统一用 `app.core.base` 的 `Alias` 声明**（同时写 `validation_alias` 与 `serialization_alias`，配合 `model_config = {"populate_by_name": True}` 让驼峰与蛇形两种写法都能入参；`to_snake` 一并导出供外部复用）；`internal/schemas/` 只放业务 DTO（`xxxDTO.py`），通用的 Pydantic 工具与响应外壳（`ApiResponse`、`ListResponse`、`Alias`、`streamFrame`）统一放 `core/base/`。
- SQL：ClickHouse 查询用 `%(name)s` 参数化；SQL 模板集中在 `core/constants/scripts.py` 与 `warehouse.py`，业务代码不内联 SQL 字符串
- 缓存：使用 `internal/cache` 的两级缓存体系（L1 内存 5 分钟 + L2 Redis 1 天 + ClickHouse 版本号失效），新统计接口优先接入而非自造缓存
- 定时任务：APScheduler 注册在 `internal/tasks/scheduler.py`，任务逻辑放 `tasks/logic/`；多实例互斥用 Redis `try_lock`/`unlock`（key 进 `RedisKeys` 常量）
- 非请求任务也必须显式传递依赖：向量同步使用 `VectorSyncDependencies` 传入 Spring、VectorMapper 和 Redis；Neo4j 同步 Service 构造函数接收 Neo4j/Spring Client，由工厂负责装配；禁止在任务逻辑内部临时获取或创建基础设施
- 权限装饰器保留 `@requireAdmin` / `@requireSelf` 语法，同时支持传入 `admin_checker` 检查器；检查器通过 `build_admin_checker(client)` 从外部 Client 创建，禁止让装饰器绕过依赖装配直接固定 Client
- 远程调用：统一 `core/client/call_remote_service`（httpx 共享连接池 + SimpleCircuitBreaker 熔断 + tenacity 重试 + 上下文头自动注入），按服务在 `internal/clients/` 封装 Client 类。两个共享 `AsyncClient`（内网 `trust_env=False`、外部抓取走系统代理）在 `lifespan.py` 创建、`yield` 之后 `aclose()` 释放，**新增客户端必须走同一处创建与释放**，不要另建模块级客户端
- ClickHouse ORM 会话的唯一入口是 `core/db/clickhouse.py` 的 `clickhouse_session()`（`get_clickhouse_db` 复用它）。**粒度保持"每查询一个会话"**：`crud/user.py` 有 `asyncio.gather` 并发跑两条 CH 查询，而 `AsyncSession` 不支持并发复用；非请求链路用引擎级 `execute_clickhouse_query` / `execute_clickhouse_sql`
- Agent 工具经 `internal/agents/toolFactories.py` 的 `AgentToolFactories` 注入 `BaseAiService`（**传工厂而非实例**，以保留线程池并行加载与单组失败隔离）
- Agent 工具权限：`internal/agents/toolScope.py` 的 contextvars 作用域（**fail-closed**）——`intentRouter` 在路由前统一写入 `ToolScope(user_id, is_admin)`，SQL 与 MongoDB 工具执行前校验行级范围（查询必须含 `user_id` 且绑定值等于当前用户，admin 放行）。禁止把请求态写进 `@lru_cache` 单例的实例字段
- 日志：`from app.core.base import Logger`，`Logger.info/warning/error/debug`
- 上下文：`core/middleware/contextMiddleware.py` 的 contextvars（`get_current_user_id` 等），深层函数免参读取用户信息
- **OpenAPI 文档定制放 `core/swagger/` 包**（实现 `openapi.py`，由 `__init__.py` 导出 `setup_openapi`，调用方只 `from app.core.swagger import setup_openapi`），在 `create_app()` 里紧随 `instrument_fastapi(app)` 调用；由它覆写 `app.openapi`，使用 `SwaggerConfig.OPENAPI_VERSION` 生成并缓存到 `app.openapi_schema`。禁止在 `app.py` 内联 `custom_openapi`（与 NestJS `app/swagger.ts`、GoZero `boot/swagger.go`、Spring `config/SwaggerConfig` 对齐）
- **HTTP 中间件一律放 `core/middleware/`（`XxxMiddleware` 继承 `BaseHTTPMiddleware`），在 `core/middleware/__init__.py` 的 `middlewares` 列表统一注册，禁止在 `app.py` 用 `@app.middleware("http")` 内联**：`add_middleware` 会把后注册的放到最外层，列表因此按「内层 → 外层」声明（当前为 `[MetricsMiddleware, ContextMiddleware]`，跑出来 `Context → Metrics`）；现有两个中间件分别是 `contextMiddleware.py`（上下文/contextvars）与 `metricsMiddleware.py`（Prometheus `mix_http_*` 指标，路由取自 `request.scope["route"]`，必须在 `call_next` 之后读取）
- **类与函数必须带单行中文 docstring**（风格参考 `internal/models/warehouse/base.py`）：类说明职责，方法/函数说明做什么，`__init__` 说明注入了哪些依赖；常量类 `@staticmethod` 用一句话概括消息/常量用途，SQL 模板常量概括查询目的；单行书写、结尾不加中文句号（对齐通用规则 13）；私有方法（`_` 前缀）与嵌套类同样要求，已存在的 docstring 不改写。新增类和函数遗漏 docstring 视同未完成；交付前可用 AST 复核（遍历 `ClassDef` / `FunctionDef` / `AsyncFunctionDef`，`ast.get_docstring` 为 None 的清单必须为空）

## GoZero 服务（gozero/，API-First）

### API-First 流程（强制）

1. 先在 `gozero/api/` 修改 `.api` 文件：`main.api` 按业务分组 import（chat、search、sqlTools、task 等），路由写在分组文件中，`@server` 块声明 `group`、`prefix`、`middleware`
2. 生成代码：`gozero/script/goctl/genApi.sh`（bash）或 `genApi.ps1`（PowerShell），两者等价，顶层入口 `scripts/goctl-api-init.sh`。核心动作是 `goctl api format -dir .` + `goctl api go -api main.api -dir ../app --style=goZero --home ../template`；脚本会自动备份并还原 `main.go` 与 `etc/`、删除生成的 `app.go`，随后清理 goctl 生成的小写中间件骨架并调用 `scripts/format.sh gozero` 收敛格式
3. ORM：`gozero/script/goctl/genOrm.sh` / `genOrm.ps1`（`goctl model mysql ddl --style goZero --home ../template`），SQL DDL 放 `gozero/script/sql/`；实际执行生成时同样会调用 `scripts/format.sh gozero`
4. 模板在 `gozero/template/`，只保留 `api/` 与 `model/` 两个目录（goctl 其它子命令的默认模板已删除），生成代码基于模板；禁止手写 handler/types 绕过生成流程，logic 文件头部有 `// Code scaffolded by goctl. Safe to edit.` 标记可编辑
5. 生成脚本已自动处理、不需要手工介入的事项：
   - **小写中间件骨架**：goctl 会把 `.api` 里声明的 `XxxMiddleware` 转成全小写开头的文件名（`userContextMiddleware` → `usercontextMiddleware.go`），与仓库手写的 camelCase 文件重名并造成中间件构造函数重复声明、编译失败。脚本只删除同时满足「位于 `app/internal/middleware`」「同目录存在忽略大小写后重名的另一个文件」「内容含 goctl 骨架占位注释」三个条件的文件，避免误删真实实现
   - **格式与行尾**：脚本最后调用 `scripts/format.sh gozero`（即 `golangci-lint fmt` + `goctl api format`，Go 代码与 `.api` 文件一起收敛）。仓库行尾由根目录 `.gitattributes` 的 `* text=auto eol=lf` 统一为 LF，不再需要手工转换或还原
6. 生成产物校验：`./mix lint gozero` 会先校验 `.api` 文件格式（`goctl api format` 没有只读模式，脚本把 `gozero/api/` 复制到临时目录执行格式化后与仓库文件 diff，不一致即失败，仓库文件只读），再调用 `gozero/script/goctl/checkGenerated.sh`，在临时模块里用 `gozero/template` + `main.api` + `gozero/script/sql` 重新生成后逐个比对
   - 带 `// Code generated by goctl. DO NOT EDIT.` 标记的文件（`types.go`、`routes.go`、`*_gen.go`）内容必须与模板生成结果一致，人工改动或删除都会报错并打印 diff
   - 带 `// Code scaffolded by goctl. Safe to edit.` 标记的文件只校验首行标记未被改写或删除，文件内容不限；与生成骨架同名但从未带过标记的手写实现（如 `recoveryMiddleware.go`）会跳过校验
   - 校验失败时不要手工改生成文件，改用 `./mix goctl-api` / `./mix goctl-orm` 重新生成；goctl 或 go 未安装时该步骤跳过并提示
   - goctl 生成路由分组的顺序存在小概率抖动，脚本会在比对不一致时重新生成最多 3 次再判定，避免把工具抖动误判为人工改动
7. 仍需人工确认的事项：
   - 已存在的 handler / logic 会被跳过（`exists, ignored generation`），**模板改动不会回灌到已有文件**：`template/api/handler.tpl` 的 `ApplyApiLog` 描述参数如今是 `constants.API_LOG_PENDING_DESCRIPTION` 占位（存量 handler 都换成了具体的 `constants.API_LOG_*`），所以「重新生成」只对**缺失**文件安全，改了 `handler.tpl` 必须手工同步存量 handler
   - `goctl model mysql ddl` 会**覆盖**已存在的 `<table>.go` 自定义文件，手工写在其中的业务方法会丢失（如 `app/model/chatMessages/chatMessagesModel.go` 的 6 个业务方法），执行 `genOrm.sh -s` 前先备份
   - 生成后跑 `cd gozero/app && GOTOOLCHAIN=local go build ./... && go vet ./... && go test ./... -count=1` 确认模板不变量未被破坏

### 目录组织与硬性约定

```
app/internal/boot        启动（Run/CreateServer）
app/internal/config      配置结构体
app/internal/handler     goctl 生成的路由与 handler（routes.go 挂中间件）
app/internal/logic       业务逻辑（按业务分目录：chat、search、sqlTools、task）
app/internal/middleware  中间件（usercontext、internalservice、recovery、apilog）
app/internal/svc         ServiceContext 组合根（分域上下文 + dependencyManifest 依赖清单校验）
app/internal/client      按服务封装的远程客户端（fastapiClient、nestjsClient、springClient）
app/internal/types       请求响应类型（goctl 生成的 types.go，校验标签在 .api 声明）
app/internal/hub         实时通信（chatHub、sseHub、chatRealtimeDispatcher、realtimeTypes）
app/internal/task        定时任务（cron 调度器 + logic/esSyncerTask）
app/common/constants     常量（messages.go、defaults.go、validations.go、httpCode.go、sqlTools.go、scripts.go、redisKeys.go）
app/common/keys          context key（未导出类型）
app/common/client        ServiceDiscovery 统一远程调用（rest/httpc 发送 + Nacos 轮询 + 退避重试）
app/common/validation    请求参数校验器（httpx.Validator 适配器、自定义规则与中文消息）
app/common/exceptions    业务异常类型（BadRequest / InternalServerError 等）
app/common/pubsub        Redis Pub/Sub 跨实例广播（redisPubSub.go）
app/common/utils         ZeroLogger 与工具（response、redisLock、internalToken、safeGo）
app/common/testkit       只依赖 common 的测试脚手架（日志器、共享用例），不参与生产链路
app/internal/testkit     依赖 internal 的测试脚手架（ServiceContext/Hub 装配、模型替身），不参与生产链路
app/model/<table>        数据模型（goctl 生成 _gen.go + custom 扩展文件）
```

- **分层方向单向**：`internal/*` 可依赖 `common/*`，`common/*` **不得**依赖 `internal/*`。实时帧类型定义在 `.api` → `internal/types`，hub 因此放在 `internal/hub`；若放 `common/hub` 就会产生反向依赖
- logic 中禁止 SQL：数据访问全部封装在 `app/model/`，logic 通过 `l.svcCtx.XxxModel.Method(l.ctx, ...)` 调用；model 方法第一个参数是 `ctx`
- svc 分域：`ServiceContext` 匿名嵌入 `RuntimeContext`、`InfrastructureContext`、`ModelContext`、`HubContext`、`ClientContext`、`LoggerContext`、`MiddlewareContext`；新增依赖加入对应分域，在 `serviceComponentsContext.go` 组装，禁止往 ServiceContext 平铺字段
- **定时任务调度器挂在 `RuntimeContext.TaskScheduler`**（从包级变量收口）：`internal/task` 提供 `NewTaskScheduler(svcCtx, lockFactory) *cron.Cron`，Redis 锁工厂由 `boot/server.go` 传入，任务每次运行通过工厂创建锁对象；返回值由 boot 赋给 `ctx.TaskScheduler`。停止统一由 `ServiceContext.Close()` 承担（先 `TaskScheduler.Stop()` 再 `Cancel()`），`boot/init.go` 的关闭入口调 `ctx.Close()` 而非直接操作调度器。**不要再引入包级调度器变量**（测试无法替换、生命周期不受 Close 管理）。cron 表达式用标准 5 字段（分 时 日 月 周），"每小时"是 `0 * * * *`，写成 `* * */1 * *` 会变成每分钟执行
- 实时 Hub 由组合根创建：`newHubContext` 创建 `SSEHub` 和 `ChatHub`，`ChatHub` 持有自己的 `ChatQueue`；禁止恢复包级 Hub、队列或其他运行态单例。需要在连接生命周期中清理状态时，Client 必须持有所属 Hub 引用
- `ServiceContext.Close()` 是唯一的关闭入口；新增需要释放的资源时把释放逻辑加进 `Close()`，不要另建包级 stop 函数
- 日志：logic 结构体嵌入 `*utils.ZeroLogger`（构造时 `ZeroLogger: svcCtx.Logger.WithContext(ctx)`），调用 `l.Info/l.Errorf/l.Error`；logx 全局方法仅限启动阶段（logx 无 Warn/Warnf）；项目 ZeroLogger 提供 `Warningf`，警告级日志用它，异常一律 `l.Errorf`。`template/api/logic.tpl` 已与这套写法对齐；模板里那行 `var _ = logx.Logger{}` 是为了消化 goctl 无条件注入的 `logx` 导包（不引用会编译报「导入但未使用」），不要当成无用代码清理
- 并行：`mr.Finish`，每个任务为 `func() error`，结果写入闭包局部变量，任务内部吞错返回 nil（错误在任务外统一处理）
- context：一切可能阻塞的函数第一个参数接收 `context.Context`，嵌套调用透传同一 ctx；logic 用 `l.ctx`
- 中间件：`.api` 文件 `@server middleware:` 声明 + `routes.go` 的 `rest.WithMiddlewares`；内部服务接口必须挂 `InternalServiceMiddleware`（校验 `X-Internal-Token`）
- 远程调用：统一走 `common/client` 的 `ServiceDiscovery.CallService(ctx, serviceName, path, RequestOptions)`，按目标服务在 `internal/client/` 封装 Client 结构体，logic 里禁止直接发 HTTP。发送层是 go-zero 的 `rest/httpc`，服务发现/负载均衡/重试/响应解析仍由自己实现，详见下面「远程调用（httpc）」小节
- 常量：消息进 `app/common/constants/messages.go`，动态部分 `fmt.Sprintf(constants.XXX+": %v", err)` 拼接
- **顶层 type 与 func（含方法）必须带单行中文前置注释**（风格参考 `internal/hub/chatHub.go` 的 `// WebSocket客户端` 与 `// ConfigureReadMarker 在服务装配阶段注入消息已读操作`）：函数/方法以函数名开头（如 `// NewChatHub 创建聊天 Hub 并初始化空队列`），类型/接口直接描述职责；单行书写、结尾不加中文句号；`type (...)` 分组块内的成员同样要求；goctl 生成文件（`types.go`、`routes.go`、`*_gen.go`）不加注释，`_test.go` 不要求。新增声明遗漏注释视同未完成
- 构建校验：`cd gozero/app && GOTOOLCHAIN=local go build ./... && go vet ./... && go test ./... -count=1` 必须通过；**必须带 `GOTOOLCHAIN=local`**（对齐 Docker 的构建约束，避免 toolchain 自动升级掩盖版本漂移）；检查未使用导包与变量；产物命名与入口一致；格式与静态检查统一走 `./mix lint gozero`，不要用裸 `gofmt -l`（对行尾差异会报大量假阳性），也不要直接 `gofmt -w` 做全量重排

### 请求参数校验

- **机制：go-playground/validator 标签式校验**。标签写在 `.api` 字段上，随 goctl 生成进 `internal/types/types.go`；**不再有手写的 `<domain>Validate.go`**，新增请求类型不需要补任何 Go 代码
- 生效链路：`boot.CreateServer` 调 `validation.InitValidator()` → `httpx.SetValidator` 注册 → `httpx.Parse` 在解析完 path/form/header/json 后触发校验。**请求类型绝不能实现 `Validate() error`**：`httpx.Parse` 是 `if 实现接口 { ... } else if 注册的校验器 != nil { ... }`，一旦实现了方法就会走前一个分支，让 `SetValidator` 静默失效（本项目踩过这个坑）
- | 自定义标签（实现在`common/validation/validator.go`）： | 标签                                                                                                                                              | 语义 |
  | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
  | `gt=0` / `required` 等                                 | validator 内置规则，直接用                                                                                                                        |      |
  | `notblank`                                             | 去首尾空白后非空；`required` 拦不住纯空白字符串                                                                                                   |      |
  | `positiveint`                                          | 字符串形式的正整数，用于 path 变量；`gt=0` 作用在 string 上比的是长度                                                                             |      |
  | `datetime`                                             | 符合`constants.DateTimeFormat`                                                                                                                    |      |
  | `searchmode`                                           | `keyword` / `hybrid` / `graph`，大小写与首尾空白不敏感                                                                                            |      |
  | `maxrunes=N`                                           | 按字符数限制长度；不用内置`max`，避免中文被按字节误判                                                                                             |      |
  | `notbefore=StartDate`                                  | 不早于同级指定时间字段；**跨字段校验必须用带参标签**，不要注册 struct-level validation（那需要 `common` 包导入 `internal/types`，会造成反向依赖） |      |
- 错误消息：官方 zh 翻译 + 自定义标签中文文案（常量在 `constants/validations.go` 的 `VALIDATOR_*`），字段名取 `json` / `form` / `path` 标签名，**只返回第一条错误**
- **handler 里用 `utils.HandleErrorWithCode(w, err, constants.HttpBadRequest)` 输出解析错误**，不要写成 `utils.Error(w, constants.HttpBadRequest, err.Error())`：后者会把 `*exceptions.BusinessError` 的状态码降级成硬编码的 400；`utils.HandleError` 那条分支则永远不会因校验失败而触发
- `template/api/handler.tpl` **不再生成 `req.Validate()`**，校验完全由 `httpx.Parse` 承担
- 标签只做请求边界检查（非空、长度、数值范围、格式）；业务与安全规则留在 logic（如 `sqlToolsQueryLogic.validateQuery` 的只读前缀白名单、表名白名单、强制 LIMIT + 上限），避免同一规则两处维护
- SSE / WebSocket 的 `user_id` 用 `omitempty,gt=0`：**允许缺省**（EventSource 与 WebSocket 握手无法自定义请求头，身份可能来自网关透传的 `X-User-Id`）；身份解析在 logic 的 `ResolveUserID`，handler 只负责接管连接
- `.api` 里的长度上限是字面量（如 `maxrunes=8000`），`.api` 语法无法引用 Go 常量，**改 `constants.SqlToolsMaxQueryLength` 这类常量时必须同步标签**
- 校验器是必需依赖：`InitValidator()` 失败直接 panic 拒绝启动；`internal/types/types_test.go` 的 `TestHttpxParseRunsTagValidation` 专门守护「注册的校验器确实被 `httpx.Parse` 触发」这条链路，不要删

### 远程调用（httpc）

- 入口：`common/client` 的 `ServiceDiscovery.CallService`，按目标服务在 `internal/client/` 封装 Client 结构体，logic 里禁止直接发 HTTP
- **发送层用 go-zero 的 `rest/httpc`**：`sd.service(serviceName)` 按服务名缓存 `httpc.Service`（熔断器名与链路追踪都绑定服务名），构造用 `httpc.NewServiceWithClient(名, sd.httpClient, injectContextHeaders)`。**必须用 `NewServiceWithClient` 注入项目自己的 `http.Client`**，`httpc.NewService` 内部是 `http.DefaultClient`，没有超时
- **httpc 只接管「发出去」这一段**：按服务名的熔断、OpenTelemetry span 与 traceparent 注入、`[HTTP] 状态码 - 方法 URL` 耗时日志。Nacos 服务发现、轮询负载均衡、退避重试、`{code,msg,data}` 响应体解析仍由 `ServiceDiscovery` 自己实现
- `httpc.Do(ctx, method, url, data)` 的 `data` 走 `mapping.Marshal`，**只接受结构体**（字段带 `path`/`form`/`header`/`json` 标签），传 `map[string]any` 会直接 panic。所以发送走 `sd.service(name).DoRequest(req)`，请求体继续由 `buildRequestBody` 构造
- `httpc` **不把 5xx 当错误**（只给 `resp.StatusCode`），状态码判定与 `httpStatusError` 必须保留；响应解析继续用 `json.Unmarshal`，**不要换成 `httpc.Parse`**（它不支持 `any` / `json.RawMessage` 字段，`map[string]any` 还会把数字弱化成字符串）
- 上下文头与内部令牌在 httpc 的 `Option`（`injectContextHeaders`）里注入，从 `r.Context()` 读用户身份；请求头常量统一放 `common/constants/remoteCall.go`
- 熔断打开时 httpc 抢先返回 `breaker.ErrServiceUnavailable`：`CallService` 负责转成降级文案，`shouldRetry` 对该错误返回 false（重试无意义且会持续冲击熔断器）
- 熔断判定只统计 **5xx / 超时 / 网络错误**，4xx 与业务错误码不计
- **释放链路**：`httpc.Service` 不暴露底层 `http.Client`，因此由 `ServiceDiscovery` 提供 `Close()`（内部 `httpClient.CloseIdleConnections()`）；三个业务 Client 各转发一个 `Close()`，由 `ClientContext.Close()` 汇总，最终挂在 `ServiceContext.Close()` 里。注意 `ClientContext` 的 FastapiClient / NestjsClient / SpringClient 三个字段统一为业务契约接口（`fastapiClient.Client` / `nestjsClient.Client` / `springClient.Client`，测试用 mock 实现），生命周期方法**不并入**接口，用包内 `resourceCloser` 断言处理，新增客户端时保持这条链路
- 链路追踪：`core/trace` 在包 `init()` 里已设置 `TraceContext` propagator，`rest.MustNewServer` → `ServiceConf.SetUp()` 也会调 `trace.StartAgent`，所以**不配 `Telemetry` 也会注入 traceparent**，只是 span 不上报；接入采集端只需在 `etc/application.yaml` 加 `Telemetry: {Endpoint, Batcher}`
- 客户端可观测性：httpc 每次调用都会打一条 logx 日志（4xx/5xx 为 error 级），日志量会上升，这是换取链路可视化的代价

### 实时链路（SSE / WebSocket）

- **帧结构的单一来源是 `.api`**：`ChatSSEMessage`、`ChatWsMessage` 声明在 `api/chat/stream.api`，接口的 `returns` 直接指向它们，**不要**再建空的 `XxxConnectResp` 占位类型。goctl 生成类型用 `Id / UserId / SenderId / ReceiverId / MessageId` 命名，与手写结构旧的 `ID / UserID / ...` 不同，跨用时需改字段名并把 `uint` 改 `uint64`
- hub 与实时分发在 `internal/hub`（`chatHub`、`sseHub`、`chatRealtimeDispatcher`、`realtimeTypes`）：本机连接管理 + 跨 Pod 事件分发。内部信封 `ChatRealtimeEvent` 只在对内使用，**不进 `.api`**
- **不要采用 `sse_handler.tpl` 的「每请求 chan + handler 内 flush 循环」单机模式**：跨实例广播依赖 `internal/hub` + `common/pubsub/redisPubSub.go` 的 Redis Pub/Sub，照模板改会丢掉多副本下的消息投递。Handler 保留 `upgrader.Upgrade` 与升级前的身份解析，升级后将连接交给 Hub；SSE Handler 将连接生命周期交给 `SSEHub.HandleConnection`。Hub 的消息已读回调由 `ServiceContext` 装配，不让 Handler 直接接触数据模型；接管前不得写 `w`。当前 `.api` 的 `/sse/chat` 与 `/ws/chat` 都是普通 `get` 路由，goctl 实际走 `handler.tpl` 生成
- **`common/pubsub.RedisPubSub` 是「一个实例一个频道」**：频道在 `NewRedisPubSub(client, logger, channel)` 构造时绑定，`Publish` / `Start` 都不收频道参数。内部只持有单个 `*redis.PubSub` 引用，所以**同一个实例不能订阅第二个频道**（会覆盖前一个订阅的引用、造成连接泄漏与丢消息）。需要新频道就新建实例，频道常量统一放 `common/constants/redisKeys.go`
- 心跳与初始帧属协议内容：SSE 连接建立时下发 `{"type":"connected"}`，WS 收到 `{"type":"ping"}` 回 `{"type":"pong"}`

### 搜索链路

- 流程是「召回 → 融合重排 → 切页」：`resolveRecallWindow(page, size)` 把 `page * size` 按 `SEARCH_RECALL_STEP_SIZE`（100）向上取整成 `recallSize`，ES 以 `Page=1, Size=recallSize` 取一档候选；融合后由 `pageSlice` 在内存切出目标页，`total` 始终取 ES 的 `TotalHits`
- `page * size` 超过 `SEARCH_RECALL_MAX_SIZE`（200）时退化为窗口内重排并打 `SEARCH_RECALL_DEGRADE_LOG`
- 融合归一化分母取**整个召回候选集**的最大 ES 分（同一档位内各页可比）；未被向量或图谱召回的候选用**候选集均值**填充，权重保持全局固定。禁止把缺失信号的权重按比例重分配给其余信号
- 两层权重分开看：ES 内 `script_score` 权重（`ESScoreWeight` / `ViewsWeight` / `RecencyWeight` 等）管第一层，`FusionConfig`（`VectorScoreWeight` / `GraphScoreWeight` / `HybridMinESWeight`）管第二层
- ES 搜索脚本、权重、参数名映射三件套任一拉取失败 → 整条增强链路关闭，降级为普通 ES 条件分页查询（无脚本时补 `create_at` 降序，避免 `_score` 恒为 0 时顺序不确定）；ES 召回后回填 Spring 实时统计与评分（views / likes / collects / follows / comment_scores）五路任一失败 → 该指标保留 ES 原值，不抛错
- 回填只改变返回给前端的展示值，`script_score` 在 ES 内执行、仍用文档快照里的 `ai_score` / `user_score` 打分，因此评分展示实时、排序最多滞后一个同步周期（整点 cron 或精确同步）
- **Spring 的批量统计数据是 List/VO，不是 Map**：`/articles/views/batch` 直接返回 `[{id,count}]`，`/likes|collects|focus/counts/batch` 返回 `{counts:[{id,count}]}`，`/comments/scores/batch` 返回 `[{article_id, role_scores}]`（Spring 全局 Jackson 是 SNAKE_CASE，见 `spring/src/main/resources/application.yaml`）。GoZero 侧由 `springClient` 的 `ParseArticleViewsMap` / `ParseCountsMap` / `ParseCommentScoresMap` 转成内部 Map，结构体 tag 必须与 Spring 的 VO 对齐（`IdCountVO`、`BatchCountVO`、`ArticleCommentScoresVO`）
- **解析错误必须显式暴露，禁止 `_` 丢弃**：ES 同步任务（`esSyncerTask`）解析失败直接 `*_PARSE_ERROR` 报错退出，检索回填（`es.go`）解析失败计入 `SEARCH_STATS_FILL_DEGRADE_LOG` 的 metrics。曾因 Spring 把这三个接口的返回从 Map 改成 List/VO 而 GoZero 仍按 Map 解析，错误被静默吞掉，导致 ES 里点赞/收藏/粉丝数/AI 与用户评分长期全为 0（`views` 不受影响是因为它随文章实体一起同步、回填失败时保留 ES 原值）
- 两侧候选上限必须对齐：`SEARCH_VECTOR_CANDIDATE_LIMIT` / `SEARCH_GRAPH_CANDIDATE_LIMIT` ≥ 召回上限，FastAPI 侧 `VECTOR_SEARCH_CANDIDATE_LIMIT` / `GRAPH_SEARCH_CANDIDATE_LIMIT` 同步

### 错误处理与依赖

- **禁止用错误文案做控制流**（重试 / 降级判定）：用类型化错误 + `errors.As`。`common/client/clientErrors.go` 的 `httpStatusError{StatusCode, Body}` 承载下游状态码，`shouldRetry` 集中判定（context 取消/超时、5xx、超时、拨号失败、EOF → 可重试；4xx、业务错误、读连接被重置 → 不重试）
- **平台约束**：Windows 的 `syscall` 只声明 `WSAE*`，没有 `syscall.ECONNREFUSED` 等哨兵，网络错误判定用 `net.OpError.Op == "dial"` 与 `net.Error.Timeout()`
- 依赖清单：`internal/svc/dependencyManifest.go` 的 `validateDependencies` 在基础设施装配后执行——`nacos` / `mysql` / `elasticsearch` 缺失直接 panic 拒绝启动，`rabbitmq` / `redis` / `mysql_raw` 缺失聚合一条降级警告。新增必需依赖需在清单登记
- **工具链与依赖版本锁定**：`go.mod` 的 `go` 指令是 `1.24.0`，`Dockerfile` 用 `golang:1.24-alpine3.20` 且 `GOTOOLCHAIN=local`。因此 `validator/v10` 必须停在 **v10.30.0**（v10.30.1 起要求 go 1.25），`golang.org/x/*` 也压在对应版本（crypto v0.46.0 / net v0.47.0 / sync v0.19.0 / sys v0.39.0 / text v0.32.0），否则 Docker 构建会报 `go.mod requires go >= 1.25.0`。**升级依赖后必须用 `GOTOOLCHAIN=local go build ./...` 复核**：默认的 `GOTOOLCHAIN=auto` 会静默下载并使用更高的 toolchain，让版本漂移在本地完全看不出来，本仓库踩过一次、是 Docker 构建失败才暴露的

### Swagger 文档

- 产物在 `app/docs/`：`openapi.json` 被 `docs/embed.go` **嵌入二进制**（改后需重新编译并重启才生效），`openapi.yaml` 不嵌入。两个产物名是本仓库约定（goctl 固定输出 `main.json`，由脚本改名），改动会让 embed 失效
- 生成流程 `gozero/script/swagger/genSwagger.sh`（Windows 为 `genSwagger.ps1`，两者等价，顶层入口 `./mix swag gozero`）：
  1. `goctl api swagger --api main.api --dir app/docs` 产出 `main.json`
  2. 按仓库约定改名为 `openapi.json`，并清理历史遗留的 `main.yaml`
  3. `swagger2openapi -o openapi.json -p openapi.json` 转成 OpenAPI 3（未安装时自动 `npm install -g`，PATH 不可见则退化为 `npx -y`）
  4. `python fix.py openapi.json openapi.yaml` 做后处理（需要 PyYAML）
- **不再使用 goctl 的 `--yaml`**：那份停留在 Swagger 2.0，而 JSON 已转成 OpenAPI 3，两边格式会分叉；现在 YAML 由处理后的 JSON 直接派生，两份产物内容完全等价。`fix.py` 写文件时显式 `newline="\n"`，避免 Windows 下写成 CRLF
- **`fix.py` 的输入必须是 goctl + swagger2openapi 的原始产物**，对已处理过的产物重跑不幂等：`/ws/chat` 已被剔除会把 `docs/websocket.json` 写成空数组、`/sse/chat` 的 `400` 响应键序被打乱。要改产物走 `./mix swag gozero` 全流程；只想改个别字段时直接编辑产物，不要手工重跑 `fix.py`
- `fix.py` 是生成后修补产物的固定环节，按顺序做以下修补：
  - 补中文标签定义与 `info`（`tag_mapping`、`x-author`），并把每个 operation 的 `tags` 由英文替换为中文名
  - **把规范版本固定为 `OPENAPI_VERSION`（`3.1.0`）**：产物必须留 3.1 —— 空数据响应用 `type: "null"`（`EMPTY_DATA_SCHEMA`，Apifox 靠它展示空值），而 3.0 的 `type` 只接受 `array`/`boolean`/`integer`/`number`/`object`/`string`，降到 3.0 会让该 schema 非法。**版本只在 `fix.py` 里改**，`genSwagger.sh` 与 `genSwagger.ps1` 都不再单独改写版本（曾因 sh 里多一段内联 Python 强制 3.1 后与 ps1 分叉），两个脚本改为校验产物版本是 `3.1.0`
  - **服务内嵌的 swagger-ui 必须支持 3.1**：`gozero/app/docs/` 下的 `swagger-ui.css`、`swagger-ui-bundle.js`、`swagger-ui-standalone-preset.js`、`favicon-16x16.png`、`favicon-32x32.png` 取自 `swagger-ui-dist` 5.x，由 `go:embed` 编译进二进制，**不再使用 `swaggo/files`**（该库只到 v1.0.1，内嵌 Swagger UI 4.x，渲染 3.1 会白屏）。升级 UI 时只替换这几个文件，并同步 `docs/embed.go` 的 embed 指令与 `boot/swagger.go` 的资源表；不引入 `.map` 文件
  - `boot/swagger.go` 的 `swaggerContentTypes` 显式声明内嵌资源的 `Content-Type`，不走 `mime.TypeByExtension`（Windows 上会读系统 MIME 注册表，类型不可控；`swagger-ui-bundle.js` 类型不对会被浏览器拒绝执行、同样白屏）
  - 移除 `swagger2openapi` 注入的全局 / path 级 / operation 级 `servers` 与 per-operation `schemes`（Swagger 2.0 文档没有 host，转换工具会默认补 `https://`，导致前端用错协议）
  - 剔除易变字段 `x-date`、`x-goctl-version`（`VOLATILE_FIELDS`），保证同一份 `.api` 在不同机器、不同 goctl 版本下生成结果可复现，不产生无意义 diff
  - 修正 `/sse/chat` 的 200 响应（`fix_streaming_endpoints`）：帧 schema 复用 goctl 按 `returns` 生成的 inline 结构，**同时挂到 `text/event-stream` 与 `application/json` 两个媒体类型下**，JSON 视图额外加 `SSE_FRAME_SCHEMA_TITLE` 标题（Apifox 取 schema 的 `title` 作为「返回响应」下的节点名），再补 `400` 统一错误体。**Apifox 不会渲染只声明 `text/event-stream` 的响应**（「返回响应」里只显示空的 SSE 封装结构、No schema defined）；FastAPI 侧的流式聊天同样是靠帧 schema 的 JSON 视图才画出帧字段，两边必须保持一致
  - 剔除 WebSocket 路径 `/ws/chat`（`WEBSOCKET_PATHS`）：OpenAPI 无法表达 WebSocket，留在产物里导入只会按 URL + method 多出一条无法发起握手的 GET 接口。剔除前由 `collect_websocket_endpoints` 摘出 `description` 与 `tags`，写成同级产物 `docs/websocket.json`，改由 `apifox-sync.sh` 经 Apifox CLI 的 `websocket` 命令同步（见「接口文档收尾流程」）
- **`fix.py` 内的执行顺序有硬约束**：`fix_streaming_endpoints` 必须排在 `wrap_unified_responses` 之前 —— 前者从 200 响应的原始 `content` 里取第一个带 schema 的媒体类型当作帧结构，若后者先执行，取到的会是已被包装成 `{code,msg,data}` 的 schema，帧字段全部丢失。`drop_websocket_paths` 放最后
- GoZero 的 handler 模板会在运行时通过 `utils.Success/Error` 输出统一外壳 `{code,msg,data}`，而 `goctl api swagger` 只生成 `returns` 对应的 `data` schema；因此 `fix.py` 必须对 `application/json` 响应补齐该外壳，并保持重复执行幂等。**跳过规则必须按内容类型显式判断：响应 `content` 里含 `text/event-stream` 就整条跳过**，不能依赖「没有 `application/json` 就自然跳过」——`/sse/chat` 的 200 同时声明两种媒体类型，沿用旧的隐式判断会把帧 schema 包进统一外壳。修改 `.api` 或响应模型后必须重新生成 JSON/YAML，检查响应 schema 的 `data` 是否仍为原始业务结构，以及 `/sse/chat` 的帧字段是否仍在
- GoZero 的 `xxxResp` 按前端兼容规范保留业务 `Data` 字段并声明 `json:"data"`；handler 必须使用 `utils.Success(w, resp)`，由 `utils.Success` 识别并展开响应对象的 `Data` 字段，最终统一输出单层 `{code, msg, data}`，禁止产生 `data.data`。Swagger 后处理也必须同步展开该字段，保证文档与运行时响应一致。
- **`fix.py` 的 `hoist_inline_models` 会把内联请求体与响应提升为 `components.schemas` 具名模型**，响应位置改为 `$ref` 引用。命名规则：`<服务前缀><路径><方法><状态码>Response/Request`，例如 `GozeroSqlToolsQueryPostRequest`、`GozeroSearchGetResponse`；路径参数保留为 `ByXxx` 片段（`/search/history/{user_id}` → `GozeroSearchHistoryByUserIdGetResponse`），状态码非 200 时才追加。两条例外必须保持内联：`text/event-stream` 的事件流响应（Apifox 靠内联帧 schema 的 `title` 渲染流式响应）、`multipart/form-data` 请求体。<br>**提升步骤必须排在 `drop_websocket_paths` 之后**，否则被剔除的 WS 响应会在 `schemas` 里留下无人引用的孤儿模型
- 改完 `.api` 后按「接口文档收尾流程」重新生成并提交产物

## 服务间内部接口与无效接口清理

「内部接口」= 只给其它服务调用、靠内部令牌 `X-Internal-Token` 鉴权、并在网关侧被 `block-internal` 挡住外部访问的接口。四个服务的识别方式与校验实现：

| 服务    | 标记方式                                                                                        | 校验实现                                         | 网关侧                  |
| ------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------ | ----------------------- |
| Spring  | `@RequireInternalToken`                                                                         | 切面 `RequireInternalTokenAspect`                | `block-internal` 黑名单 |
| NestJS  | `@RequireInternalToken()`                                                                       | `framework/guards/internalToken.guard.ts`        | 同上                    |
| FastAPI | `@requireInternalToken`（装饰器会给 wrapper 打 `requires_internal_token` 标记，供契约测试自省） | `core/decorators/requireInternalToken.py`        | 同上                    |
| GoZero  | `.api` 的 `@server middleware:` + `InternalServiceMiddleware`                                   | `common/middleware/internalServiceMiddleware.go` | 同上                    |

### 判定「无效内部接口」的流程（清理前逐步执行）

1. **列全路径**：`类级 @RequestMapping/@Controller` 前缀 + 方法级路径拼成完整路径，路径参数写成模板（`/users/by-github-id/{githubId}`）；GoZero 以 `.api` 里的 `@handler` 路径为准
2. **全仓检索调用方**：其它三个服务的 client 封装（`infra/client`、`internal/client`、`internal/clients`、`common/client`）、`gateway/apisix/apisix.yaml`、`scripts/`、各服务测试目录。Spring/NestJS 必须**同时对照「接口声明 + 实现」两处**，GoZero 对照 `.api` 与 handler
3. **区分引用性质**：只出现在 `*_test.go` / `*.spec.ts` / `src/test` 的**不算调用方**；测试里为满足接口而写的 stub 方法同理
4. **判断定位，别直接删**：
   - 本该服务外部（前端语言契约、APISIX 可达）→ **去掉内部令牌对外化**（例：`/chat/send` 普通聊天），并确认网关黑名单不再拦它
   - 确实只服务服务间调用且无消费者 → 删除
5. **连带清理只服务它的实现**：Service 方法 → Mapper/Repository 查询方法 → 请求/响应 DTO → 测试用例；删除过程中每一层都要重新确认「是否还有其它调用方」
6. **任务类的手动触发接口一律保留，不纳入清理范围**：`/task/*` 这类手动触发入口（Spring `TaskController`、NestJS `TaskController`、FastAPI `taskRouter`）是运维兜底能力——手工补跑、修数据、紧急刷缓存都靠它。**即使当前没有任何服务调用、也即使 `@Scheduled`（Spring）/ `@Cron`（NestJS）/ scheduler（FastAPI）已在自动调度，都必须保留**：自动调度是常态通道，HTTP 入口是运维通道，两者互补（曾误删 `POST /task/clean`、`/task/apilog`、`/task/articlelog`、`/task/update-analyze-caches`、`/task/init-hash-cache`、`/task/clear-analyze-caches`）
7. **重新生成产物并同步文档**：`./scripts/swag-init.sh <service>`（可选 service 名），需要时 `./mix apifox`。**Spring 删过控制器源文件后必须先清掉 `target/classes` 下的残留 `.class`**——Maven 增量编译不删除已移除源文件的产物，文档生成器扫描 classpath，否则已删接口会继续出现在产物里

### 已清理的无效内部接口（勿重复排查）

| 服务    | 已删除                                                                                                                                                                                                                              | 已对外化                                                                                                                                           |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Spring  | `GET /users/by-github-id/{githubId}`（连带 `UserService.findByGithubId` 接口+实现）、`GET /focus/statistics/monthly-trend/{userId}`（连带 `FocusService.getMonthlyFollowTrend`、`FocusRepository.countMonthlyByUserIdGroupByDate`） | —                                                                                                                                                  |
| FastAPI | `POST /ai_history`、`GET/PUT/DELETE /ai_history/internal/{id}`（连带 `AiHistoryService`/`AiHistoryMapper` 各 3 个方法与 `CreateHistoryDTO`/`UpdateHistoryDTO`/`DeletedResponse`）                                                   | `POST /chat/send`：去掉 `@requireInternalToken` 作为普通聊天接口，补 `tests/internal/api/chat/chatRouter_test.py` 固化「聊天接口不带内部令牌」契约 |
| NestJS  | `POST /article-logs`、`POST /api-logs`（连带两个 Service 的 `create`）                                                                                                                                                              | —                                                                                                                                                  |
| GoZero  | 无（`/task/syncer`、`/sql-tools/tables`、`/sql-tools/query` 均有生产调用方）                                                                                                                                                        | —                                                                                                                                                  |

### 必须保留的接口（勿当死代码清理）

`/task/*` 手动触发接口一律保留，判定「无效内部接口」时直接排除：

| 服务    | 接口                                                                                                | 保留理由                                                                                                     |
| ------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Spring  | `POST /task/clean`（`TaskController`）                                                              | 手动触发过期 Token 清理；`TokenCleanupTask` 的 `@Scheduled(cron = "0 0 * * * *")` 是常态通道，接口是运维通道 |
| FastAPI | `POST /task/vector`、`POST /task/sync-neo4j`、`POST /task/sync-warehouse`                           | 手动补跑向量 / 图谱 / 数仓同步（Spring 的同步切面也会按 ids 触发同一入口）                                   |
| FastAPI | `POST /task/update-analyze-caches`、`POST /task/init-hash-cache`、`POST /task/clear-analyze-caches` | 手动刷分析缓存、初始化文章内容 hash 缓存、清空分析缓存；scheduler 自动跑同一批函数，接口用于紧急修复         |
| NestJS  | `POST /task/apilog`、`POST /task/articlelog`                                                        | 手动清理超期 API 日志 / 文章日志；`TaskService` 的 `@Cron` 是常态通道                                        |
| GoZero  | `POST /task/syncer`                                                                                 | 按 ids 精确同步 ES（Spring 同步切面在用），同时是手动全量重刷入口                                            |

**删除时容易误伤的保留项**（都已确认仍在使用，勿再删）：FastAPI 的 `create_ai_history`（流式聊天保存历史）、`update_analyze_caches_async` 与 `initialize_article_content_hash_cache_async`（scheduler / vectorSyncTask，以及 `/task/update-analyze-caches`、`/task/init-hash-cache`）、`ChatRequest`（被 `ChatStreamRequest` 继承）、`ChatResponseData`（被 `ChatResponse` 引用）；NestJS 的 `CreateArticleLogDto` / `CreateApiLogDto`（RabbitMQ 消费者攒批 `insertMany` 在用）；各 Cache 的 `clear_all()`（被 `/task/clear-analyze-caches` 调用）。

## 网关（gateway/，Apache APISIX）

- 以 YAML 数据面运行（`role_data_plane` + `config_provider: yaml`），无业务代码；路由与插件全部在 `apisix/apisix.yaml`
- 静态文档：`gateway/swagger-ui` → `/swagger-ui/`（Swagger UI，可在线调试），由 `nginx_config.http_server_configuration_snippet` 的 `location` + compose 挂载提供；新增静态目录按同一模式加 volume 与 `location`
- Swagger UI 页面自带「导出 Markdown」按钮：`gateway/swagger-ui/markdown-export.js` 在浏览器里把页面上已加载的各服务规范（Tab 上的 `data-url`，即 `/swagger/*.json`）实时转成 Markdown 并下载，**不依赖仓库里任何预生成文件**；改导出格式只改这个脚本，四个服务新增接口无需重新生成产物
- **认证外置**：业务路由挂 `forward-auth` 回调 Spring 的 `/users/internal/auth/validate`，由网关注入 `X-User-Id` / `X-Username` / `X-Session-Id` 供下游透传；**下游服务只信任请求头**，不自行解析 JWT
- 内部接口防护靠 `block-internal` 路由（URI 黑名单），新增内部接口必须同步加入黑名单
- **`block-internal` 的 `uri` 是精确匹配**（只有以 `*` 结尾才是前缀匹配），而它要挡的接口往往落在宽松前缀路由（`/articles/*`、`/users/*`、`/email/*`、`/ai_history/*`）覆盖范围内。新增内部接口时除了加黑名单，还要确认黑名单条目能覆盖实际访问路径，否则会出现「精确路径被挡、子路径可直达」的缺口
- 长连接用独立 upstream（读超时 3600s），与普通接口区分
- 新增对外路由：按既有分组挂 `forward-auth` 与 `limit-req`（登录类用 `*login_limit`）；public 路由必须有明确理由且不能漏挂限流
- 改配置后用 YAML 解析器校验语法，并确认目标路由的插件确实挂载
- **端口暴露**：根 `docker-compose.yml` 里只有 gateway 映射宿主机（8080 → 容器 9080），spring / gozero / nestjs / fastapi **均不映射宿主机端口**，容器间经 `hcsy` 网络 + Nacos 直连。下游无条件信任 `X-User-Id`，所以这个收敛状态正是身份不可伪造的前提，改动编排时不要给业务服务加回 `ports`；本地开发模式（`./mix dev seq`）直连服务端口，没有这层保护

## 仓库工程约束

- **禁止删除、清空、移动或重建本地依赖环境**：`fastapi/.venv`、`nestjs/node_modules` 属于开发者本机已安装的依赖环境，删除与整体重建都是禁止操作（重装需联网且耗时，也会打断本地校验命令）；排查问题、清理临时文件、执行格式化与校验时一律绕开这些目录，确需变更依赖时用对应包管理命令做增量安装。**不要为了任何理由运行删除 `.venv` 的命令**（含 `rm -rf`、`Remove-Item -Recurse`、`uv venv --clear`、`python -m venv --clear` 等）
- **Windows 主机上禁止用 WSL 的 bash 跑 `./mix compile fastapi` 与 `./mix test fastapi`（本问题只在 Windows + WSL 场景出现，Linux/macOS 无此问题）**：这两步底层分别是 `uv run python -c ...` 与 `uv run pytest`。在 Windows + WSL 的组合下，WSL bash 里 `uv` / `ruff` / `python3` 解析到的是 Linux 版本，`fastapi/.venv` 却是 Windows 的 uv 创建的（`pyvenv.cfg` 里 `home = C:\...`）；Linux uv 判定环境与自身平台不匹配后，会按 `uv run` 的 sync 语义**清空并重建 `.venv`**，一旦中途被打断就留下半成品，`fastapi/pyproject.toml` 的 `venvPath = "."` / `venv = ".venv"` 随即解析失败并回退到根目录或全局解释器，表现为「IDE 只能解析到根目录的环境」，等价于「重建本地依赖环境」，属禁止操作。Linux/macOS 上 `uv` 与 `.venv` 同平台，`uv run pytest` 就是正常入口，不受本条约束
  - 正确做法（Windows）：`./mix` 只在 Windows 侧 shell（Git Bash 或 PowerShell，且 PATH 指向 Windows 工具）执行；fastapi 的校验改用项目自带解释器做只读操作——`fastapi/.venv/Scripts/python.exe -m pytest -q`、`fastapi/.venv/Scripts/python.exe -m ruff check .`，以及 `scripts/compile.sh` 里那段字节码编译片段。macOS/Linux 上按默认命令执行 `uv run pytest` 即可
  - 全服务形式同样禁止（Windows + WSL 场景）：`./mix compile`、`./mix test` 会把 fastapi 一起带上，要么写明确的服务名、要么改用 Windows 侧 shell
  - 唯一例外是技能同步：`./mix skills` 只在技能目录间做镜像复制，不碰依赖环境，在 WSL bash 下可用 `HOME=/mnt/c/Users/<user> ./mix skills` 显式指定目标（见本节的技能同步条目）；除此之外不要自行执行 `uv run` / `uv sync` / `uv venv`
- **Windows 主机上出现下列任一信号就停止用 WSL bash 跑 `./mix`，改到 Windows 侧 shell（同样只在 Windows + WSL 下出现）**：`./mix skills` 把技能同步到 `/home/<user>` 而不是 `C:\Users\<user>`（IDE 看到的技能没更新）、`./mix lint gozero` 报 golangci-lint「未安装」而本机其实已安装、`./mix format fastapi` 实际调用的是 Linux ruff。三者都是「bash 解析到了 Linux 工具链」的同一根因，在 WSL bash 下继续跑 `./mix compile` / `./mix test` 就会踩到重建 `.venv` 那条
- 行尾由根目录 `.gitattributes`（`* text=auto eol=lf`）统一为 LF，仓库不再按 CRLF 维护；新建文件不需要手工转换行尾
- 格式化统一走各服务的工具（`./mix format`）：Spring Spotless、GoZero golangci-lint + goctl api format、NestJS Prettier、FastAPI Ruff；不要再手工执行 `gofmt -w` 或 `prettier --write` 做全量重排
- Go 的格式问题用 `./mix lint gozero` 判断（golangci-lint 的 gofmt formatter），不要用裸 `gofmt -l`：它对行尾差异会报大量假阳性
- `goctl`（`api format` / `api go`）生成后由 `genApi.sh` / `genOrm.sh` 自动调用 `./mix format gozero` 收敛格式；手工执行 goctl 时兜底跑一次即可，不需要手工处理行尾
- **goctl 版本不进产物**：`gozero/template/**` 与仓库已生成文件都不包含版本注释（`// goctl {{.version}}`、`//  goctl version: x.y.z`），同一份 `.api` 在不同 goctl 版本下生成结果一致，不会产生无意义的版本 diff；产物是否被人工改动由 `./mix lint gozero` 校验
- **不要在仓库根目录直接执行 goctl**：goctl 在 Windows 下判定模块有缺陷（`go env GOMOD` 返回 `NUL` 而非 `/dev/null`），会以调用者的当前目录为基准回退执行 `go mod init`、`go work use`，在仓库根目录执行会生成多余的 `go.mod` 并把 `go.work` 改成 `use (. / ./gozero/app)`；`./mix goctl-orm`、`./mix goctl-api` 目前仍会触发，执行后确认 `git status` 并清理、还原这两个文件。手工执行 goctl 时先 `cd` 到模块内（如 `gozero/app`）；`checkGenerated.sh` 的生成阶段已切到临时目录执行，不受影响
- git 用于精确核对与回退：`git status --porcelain`、`git diff --ignore-cr-at-eol`（判断是否仅行尾差异）、`git checkout -- <文件>`
- 本机环境参考：Go / gofmt 在 `C:\Program Files\Go\bin\`，goctl 在 `C:\Users\30708\go\bin\goctl.EXE`，git 在 `C:\Program Files\Git\cmd\git.EXE`（`usr\bin\` 下有 grep / tr / sed / basename 等，用完整路径调用），maven 在 `C:\apache-maven-3.9.11\bin\mvn.CMD`，javap 在 `C:\Program Files\Java\jdk-17\bin\javap.exe`
- bash 环境的 `dirname` / `head` 等不稳定（PATH 时有时无），批量格式与行尾校验优先走 `./mix format` / `./mix lint`，需要脚本兜底时用 Python `subprocess` 调绝对路径
- `mix` 脚本顶层子命令有 `setup`、`swag`、`apifox`、`apifox-readme`、`goctl-api`、`goctl-orm`、`lint`、`format`、`test`、`compile`、`token`、`hooks`、`skills`、`dev`、`dist`、`docker`、`docker-services`、`loki`、`compose`、`help`；开发模式必须写全 `./mix dev multi|seq|stop`（**没有** `./mix seq` / `./mix multi` / `./mix stop`，README 历史版本里这三处写错）
- **内部服务令牌用 `./mix token [service]` 获取，不要再靠单测打印**：只签一枚令牌（`scripts/internal-token.py`，只依赖 Python 标准库，密钥取各服务 `.env` 的 `INTERNAL_TOKEN_SECRET`）；不传服务时随机挑一个（四服务密钥一致、当前没有接口校验 `serviceName`，一枚通用），可选 `--user-id`（默认 -1）、`--ttl`（默认 24h）、`--header`、`--quiet`、`--json`、`--no-apifox`、`--dry-run`；**请求头必须带 Bearer 前缀**（`X-Internal-Token: Bearer <token>`），四个服务都会剥掉前缀再校验，漏掉会返回 401
- **`./mix token` 同时写 Apifox 变量（根目录 `.env` 配好 `APIFOX_ACCESS_TOKEN` / `APIFOX_PROJECT_ID` 时）**：默认 `apifox variables set --scope global` 写项目全局变量 `internal_token`（`--variable-name` 可改）并回读校验，Apifox 全局参数配 `X-Internal-Token: Bearer {{internal_token}}`（变量值不含 Bearer 前缀，前缀写在参数值里）；`--variable-scope environment` 时改写环境变量，**此时必须先用 `apifox export --format apifox` 回读已有 variables 再增量合并**：`environment get` / `list` 都不返回 `variables` 字段，直接 PUT 会把手工维护的变量清掉
- `scripts/run.sh` 的运行工具默认值：`--java-build` 默认 `maven`、`--node-runtime` 默认 `bun`、`--python-runtime` 默认 `uv`
- 两套容器编排的容器名不同：`./mix docker` 用 `mix-<service>-container`，`./mix compose` 用 `mix-<service>`（compose 的 `container_name`）
- `README.md` 行尾由 `.gitattributes` 统一为 LF，批量改文档按「归一化 LF → 断言唯一性后替换」处理，不要逐处手工编辑
- **数据库初始化脚本**统一放根目录 `db/<类型>/`（`mysql`、`postgresql`、`clickhouse`、`mongodb`、`es`、`neo4j`），只放表、扩展、索引、集合级别的脚本；`CREATE DATABASE` 与 `USE` 一律由使用方按需自行执行，**不在脚本中写死库名**，库名以各服务的数据库配置项为准（`DB_NAME`、`DB_MYSQL_DBNAME`、`DB_DATABASE`、`DB_MYSQL_DATABASE`、`DB_POSTGRES_DATABASE`、`DB_MONGODB_DATABASE`）。PostgreSQL 容器侧的初始库由 `scripts/docker-services.sh` 的 `POSTGRES_DB` 创建，需与 `DB_POSTGRES_DATABASE` 保持一致
- 本技能包（`skills/mix-web-demo/`，目录名与 SKILL.md 的 `name` 一致）改完后用 `./mix skills` 同步到本机 Agent 技能目录：目标清单在 `scripts/skills-targets.conf`（只列用户级 `<home>` 技能目录，可自行追加工具，仓库内项目级目录不参与），只同步技能根目录已存在的目标，同步为镜像覆盖且内容一致时跳过；`--list` 看检测结果、`--dry-run` 预演，脚本为 `scripts/skills-sync.sh`（Windows 在 Git Bash 下执行）。脚本用 `HOME`（无则 `USERPROFILE`）解析清单里的 `<home>`，因此在 WSL 的 bash 里执行会把技能写到 Linux 侧主目录 `/home/<user>`，而 IDE 读的是 `C:\Users\<user>`，看起来「同步成功」但技能并未更新（同样是 Windows + WSL 才有的问题）；Windows 下要么用 Git Bash，要么先执行 `HOME=/mnt/c/Users/<user> ./mix skills`

## 容器镜像与镜像分发

### 镜像名称、推送与版本

- `./mix docker build` 产出本地镜像 `mix-<service>:latest`（只处理 spring/gozero/nestjs/fastapi；gateway 用官方 `apache/apisix` 镜像，不构建也不推送）
- `./mix docker push --prefix <前缀> [--tag <tag>] [service...]` 把本地镜像重打标签为 `<前缀>/mix-<service>:<tag>` 后推送：**不传 `--tag` 时固定推 `latest`**，脚本没有从 Git 提交号或时间推导版本的逻辑，也不读本地镜像的实际 tag；`gateway` 直接跳过，未知服务名只警告
- 推送脚本只做 `docker tag` + `docker push`，**不执行 `docker login`**：首次推送前自行登录目标仓库

### 本地构建优先、远程镜像兜底

- 统一镜像名的开关是根目录 `.env` 的 `DOCKER_IMAGE_PREFIX`，**取值必须以 `/` 结尾**（`docker.io/yourname/`、`registry.example.com/team/`）；未配置时保持纯本地模式，行为与引入该变量前完全一致
- `docker-compose.yml` 四个业务服务的镜像写 `${DOCKER_IMAGE_PREFIX:-}mix-<service>:latest`：前缀为空退化为本地名，配置后为 `<前缀>mix-<service>:latest`，与推送出去的镜像名一致
- `scripts/build_and_run_services.sh` 在构建成功后按前缀补打同名标签，保证 compose 命中的就是本次本地构建结果；`scripts/docker-compose-up.sh` 先按有效名检查，本地构建存在但有效名缺失时补标签，两者都缺失且配置了前缀时交给 compose 拉取，未配置前缀才走本地构建
- 生效依赖 Compose 默认的 `pull_policy: missing`：本地有同名镜像直接使用，缺失才拉取。要强制以远端为准必须显式 `pull_policy: always`，代价是每次 `up` 都拉取、本地构建结果会被同名远端镜像覆盖
- build / compose-up / push 三个脚本都会在环境变量未设置时读取根目录 `.env` 的同名变量，保持同一口径
- `./mix compose up` 的本地镜像检查发生在 compose 合并逻辑之外：纯用远端镜像时直接 `docker compose up -d` 或先 `docker compose pull`，不要依赖该脚本跳过本地构建
- 本机访问 Docker Hub 失败（`failed to fetch anonymous token`、`dial tcp` 超时）时，`docker build` 与 `docker buildx build --check` 都会停在拉取基础镜像元数据阶段，这是环境问题（未配置加速或代理），不要据此判定 Dockerfile 写法有误
- **网关的 Nacos 发现只在容器创建时拉一次服务列表，之后只刷新已知服务**：若创建瞬间服务尚未注册或容器网络未就绪，个别服务会永久缺席，表现为 `/swagger/<服务>.json` 返回 503、`logs/gateway/error.log` 里 `failed to set upstream: no valid upstream node: nil`。dev 模式已加两道保护——`run.sh` 的 `wait_nacos_registration` 等四个服务注册后再起网关，`scripts/gateway-dev.sh` 启动后自检四个规范，不可达就 `docker compose restart` 重建缓存（实测 restart 稳定恢复）；手工排查时先看 `docker compose restart` 是否恢复，不要改 `apisix.yaml` 的 upstream 配置
- **docker compose 需 ≥ v2.36.0**：v2.35.x 在 `up` 时并发拉取镜像会 `fatal error: concurrent map writes`，栈顶在 `pkg/compose.(*composeService).pullRequiredImages`（docker/compose#12747，v2.36.0 修复）；`scripts/prepull-images.sh` 在 `./mix dev seq` 启动网关前与 `./mix compose up` 前用 `docker CLI` 串行预拉缺失镜像做兜底（命中缓存即跳过、失败不阻断），根治仍是升级 compose 或临时降到 ≤ v2.27.x；遇到该崩溃先看 `docker compose version`，不要改项目编排文件

### FastAPI 镜像只保留字节码

- `fastapi/Dockerfile` 为多阶段：builder 用 `python -m venv /opt/venv` 装依赖，`compileall -b -f main.py app` 后 `find /app -name '*.py' -delete`；runtime 只复制 `/opt/venv` 与 `/app`
- `-b` 是必需项：产出与源码同目录的 `main.pyc`、`__init__.pyc`（legacy 布局），删掉 `.py` 后仍可按模块名导入；不加 `-b` 时产物落在 `__pycache__/`，删源码就无法导入
- 两个阶段必须使用同一基础镜像 tag（当前 `python:3.12-slim-bookworm`），否则字节码 magic number 与 ABI 不匹配；升级 Python 版本要两处同步改
- 仍会出现在镜像中且属预期：`application.yaml`（`load_config` 按 `Path(__file__).parents[3]` 定位，`.pyc` 与 `.py` 同目录时结果一致）、`/opt/venv` 下第三方库的 `.py`、`logs/`、`static/`
- 已知边界：`.pyc` 可被反编译（提高门槛而非绝对保护）、traceback 不再打印源码行、容器内不能开 `--reload`（热重载依赖 `.py`）
- 改依赖或包结构后正常重建即可；`requirements.txt` 只在 builder 阶段需要，runtime 已删除

### .dockerignore 约定（四个业务服务）

构建上下文是服务目录本身（`docker build` 在服务目录内执行，不是仓库根目录），只排除构建与运行都不需要的内容：

- 公共项：`.env` / `.env.docker`（运行期由 `--env-file` / `env_file` 传入）、IDE 与 OS 文件、`.git`、日志目录、本地构建产物
- `spring/`：`src/test/`（`mvn package -DskipTests` 不需要测试源码，排除后不再编译测试类）、`docs/`、`logs/`、`*.md`
- `gozero/`：`api/`、`template/`、`script/`、`**/*_test.go`、`.golangci.yml`。**禁止改成 `**/docs`**：`gozero/app/docs` 的 swagger 资源由 `go:embed` 嵌入二进制，缺失会直接构建失败；现有根级 `docs/` 只匹配上下文根目录，安全
- `nestjs/`：单测与源码同目录，必须用 `**/*.spec.ts` 覆盖 `src/**`，并用 `**/*-spec.ts` 覆盖 `*.e2e-spec.ts` / `*.integration-spec.ts`。**只写 `test/` 等于没写**（当前仓库没有该目录），`test/` 仅作后续 e2e 目录的预留；`tsconfig.build.json` 本来就 exclude `**/*spec.ts`，因此排除后不影响 `nest build`
- `fastapi/`：`tests/`、`docs/`、`script/`、`*.md`
- 匹配语义是 Go 的 `filepath.Match`：`*` 不跨 `/`，所以 `*.md` 只排除上下文根目录那一层；要按任意层级排除必须写 `**/xxx`，写之前先确认目标不是编译期或运行期依赖（gozero 的 `app/docs` 就是反例）
- 改完 `.dockerignore` 或 Dockerfile 后自检：`./mix docker build <service>`，再用 `docker run --rm --entrypoint sh mix-<service>:latest -c "ls /app"` 核对内容（fastapi 追加 `find /app -name '*.py'`，预期无输出）

## 接口文档收尾流程

新增、修改或删除对外接口后，除了本服务的格式化、lint 与构建校验，还要走完「重新生成静态文档 → 同步 Apifox」两步，文档产物与服务代码在同一次提交里。

### 第一步：生成静态 OpenAPI 文档（必做）

```bash
# 只处理本次改动的服务
./mix swag spring
./mix swag gozero
./mix swag nestjs
./mix swag fastapi

# 或一次生成四个服务
./mix swag

# 直接调用脚本
./scripts/swag-init.sh spring
```

产物落在各服务自己的 `docs/` 目录，每个服务输出 `openapi.json` 与 `openapi.yaml` 两份等价文档：

| 服务    | 产物                           | 生成方式                                                | 前置工具  |
| ------- | ------------------------------ | ------------------------------------------------------- | --------- |
| Spring  | `spring/docs/openapi.json`     | `OpenApiDocGenerator` 隔离 Web 层上下文 + 依赖自动 Mock | Maven     |
| GoZero  | `gozero/app/docs/openapi.json` | `goctl api swagger` → `swagger2openapi` → `fix.py`      | goctl     |
| NestJS  | `nestjs/docs/openapi.json`     | `NestFactory.create(..., { preview: true })`            | Bun       |
| FastAPI | `fastapi/docs/openapi.json`    | 导入`create_app()` 后取 `app.openapi()`                 | uv/Python |

四个服务都是**离线生成**：不启动 HTTP 服务，不连 Nacos / MySQL / Redis / RabbitMQ，也不需要各服务的 `.env`（Spring 的 Nacos 配置拉取由 `spring/src/test/resources/bootstrap.yaml` 覆盖关闭）。对应工具未安装时该服务跳过并提示，其余服务继续生成；`gateway` 为配置驱动，无 OpenAPI 产物。

生成后核对五件事：

1. 新接口出现在产物里，路径、方法、参数与响应结构和实现一致
2. `openapi.json` 与 `openapi.yaml` 成对更新，不要只提交其中一份
3. 新增接口在 `components.schemas` 里有对应的具名模型（GoZero 看 `Gozero*`、NestJS 看 `Nestjs*` 前缀），且 `schemas` 里没有无人引用的孤儿模型；只有事件流响应与 multipart 请求体允许保持内联
4. **允许为 null 的字段必须在产物里表达成可空**，否则 Apifox「校验响应」会把合法的 `null` 判成「`$.data.xxx` 不允许为 null」。四个服务都是 OpenAPI 3.1，可空只能写成类型数组 `type: ["integer","null"]`（或 `anyOf: [{type: "integer"}, {type: "null"}]`）——`nullable: true` 是 3.0 的写法，3.1 下会被忽略（实测 `@Schema(nullable = true)` 在 springdoc 3.1 产物里没有任何效果）
   - Spring：`SwaggerConfig#markNullableProperties` 统一处理——未列入 `required` 的属性自动补 `null`；需要声明「不允许为 null」就在字段上加 `@NotNull` / `@NotBlank` / `@NotEmpty` 或 `@Schema(requiredMode = Schema.RequiredMode.REQUIRED)`（统一响应的 `code`/`msg` 已按此声明，`data` 保持可空）
   - NestJS：`app/swagger.ts#markNullableProperties` 同理——`@ApiProperty({ required: false })` 的字段补 `null`，默认 `required: true` 的不补
   - FastAPI：Pydantic 的 `Optional[X]` 已生成 `anyOf: [{type: X}, {type: null}]`，无需额外处理
   - GoZero：`script/swagger/fix.py#mark_nullable_properties` 在提升模型之后统一补——`.api` 里标了 `json:",optional"` 的字段（goctl 不写进 `required`）与切片字段（Go 的 nil slice 序列化就是 `null`）补 `null`；要让某个标量字段允许 null，在 `.api` 里给它加 `optional`，不要改 `fix.py` 的清单
5. GoZero 若改了 `.api`，确认产物里没有 `x-date` / `x-goctl-version`（出现即说明 `fix.py` 后处理没跑到）；同时确认 `gozero/app/docs/websocket.json` 里的描述与 `.api` 的 `@doc` 一致，该文件与 `openapi.json` 一样属于要提交的产物

### 第二步：同步到 Apifox（配置了令牌时执行）

```bash
# 先校验产物与配置，不发起导入请求
./mix apifox --dry-run

# 同步本次改动的服务
./mix apifox spring

# 或同步全部
./mix apifox

# 只读检查 Apifox 侧接口与数据模型的引用是否完整（断链会报 can't resolve reference）
./mix apifox-check
```

- 脚本读取的是仓库内的静态产物，**必须先完成第一步**，否则同步上去的是旧文档
- 需要根目录 `.env` 中的 `APIFOX_ACCESS_TOKEN` 与 `APIFOX_PROJECT_ID`；未配置时脚本会直接报错退出，这种情况先提交文档产物，把同步留到配好令牌的环境执行
- 按服务串行导入，输出「新增 / 更新 / 忽略 / 失败」计数；出现失败计数或非零退出码必须排查后重试，不要当成噪声放过
- 覆盖策略默认 `AUTO_MERGE`，保留 Apifox 侧手工维护的中文名、mock 与返回示例，只按文档更新结构化内容
- **同步默认以文档为准做全量对齐**：`APIFOX_DELETE_UNMATCHED_RESOURCES` 默认 `true`，对应开放 API 的 `options.deleteUnmatchedResources`，会删除**该服务导入目录内**（`APIFOX_FOLDER_*`）文档里没有的接口与数据模型（本地实测：只同步 fastapi 时项目接口总数 217 → 210，正好清掉 fastapi 目录内的 7 个残留，其它服务目录未受影响；Apifox 的 WebSocket 接口是独立资源类型，删除后仍完好）。所以删掉代码里的接口后，重新生成产物再同步即可自动清理，**不需要手工删 Apifox 接口**
- 对齐是全量覆盖语义：Apifox 侧手工新增的 HTTP 接口与数据模型会在下次同步时被清掉（`WebSocket` 与 Markdown 文档不受影响）。排查期可临时关闭：`APIFOX_DELETE_UNMATCHED_RESOURCES=false ./mix apifox <service>`；删除是真实删除，可先 `apifox export --project <id> --format apifox --scope all --output <file>` 整项目备份，误删内容可从 Apifox 回收站找回
- **警惕「AUTO_MERGE + 全量对齐」组合造成接口响应结构引用断链**：`AUTO_MERGE` 不整体重写已存在接口的响应结构绑定，而 `APIFOX_DELETE_UNMATCHED_RESOURCES=true` 会删除文档里已不存在的数据模型。当模型命名变化（例：Spring 补 Swagger 注解后 springdoc 改变 `Result«XxxVO»` 的生成名）时，接口上残留的 `$ref` 仍指向被清理的旧模型，Apifox「校验响应」报 `can't resolve reference #/definitions/<数字ID> from id http://json-schema.org/draft-04/schema#`（数字 ID 是 Apifox 数据模型的内部 ID，产物本身引用链完好）。**已由脚本自动切换**：`apifox-sync.sh` 为每个服务计算 `components.schemas` 的规范化 sha256（只关心模型本身，与排版、字段顺序、paths 调整无关），与 `.apifox-state/<service>.schemas.sha256` 里上次成功同步的指纹比对——指纹变化或首次无记录时，该服务本轮自动切到 `OVERWRITE_EXISTING` 并打印原因；指纹未变则保持默认 `AUTO_MERGE`。显式设置了 `APIFOX_ENDPOINT_OVERWRITE_BEHAVIOR` / `APIFOX_SCHEMA_OVERWRITE_BEHAVIOR` 时以显式值为准、不做自动切换；只有导入成功才写回指纹，失败保留旧值以便下次重试。**`.apifox-state/` 必须随仓库提交**：它记录的是「共享 Apifox 项目当前已同步到哪个模型版本」这一远端基线，不是本机状态。漏提交会让其他机器的指纹停留在旧值、误判为「模型有变」而触发覆盖同步，把已保留的手工 Mock 与示例冲掉；同理，同步成功后要与 `docs/` 产物一起提交它。**手工修复**（自动机制被显式配置绕过时）——`APIFOX_ENDPOINT_OVERWRITE_BEHAVIOR=OVERWRITE_EXISTING APIFOX_SCHEMA_OVERWRITE_BEHAVIOR=OVERWRITE_EXISTING ./mix apifox <service>`，跑完恢复默认 AUTO_MERGE；代价是该服务接口上手工维护的参数说明、Mock 与示例会被产物覆盖。应急也可在 Apifox 接口「返回响应 → 数据结构」里手工重新绑定现行数据模型。预防：凡是重命名/调整 VO 或响应包装导致 springdoc/文档生成器模型名变化，同步前先跑一次 OVERWRITE_EXISTING 再回到 AUTO_MERGE
- 导入前会为**本轮文档新增**的接口补写 Apifox 责任人扩展 `x-apifox-maintainer`（值取团队内昵称或用户账户名），默认取 `APIFOX_ACCESS_TOKEN` 对应账号的用户名；可用 `APIFOX_MAINTAINER` 显式指定，或用 `--no-maintainer` 关闭填充
- **数据模型目录必须按服务隔离（`can't resolve reference` 的根本修复）**：`deleteUnmatchedResources` 的清理范围是「该服务的导入目录」。接口早有 `APIFOX_FOLDER_<服务>` 按服务分开，但数据模型此前都落在项目根目录，于是任一服务的全量对齐都会删掉其它服务刚同步的模型，而接口上的 `$ref` 不会回滚 —— 产物本身引用链完好，Apifox「校验响应」却报 `can't resolve reference #/definitions/<数字ID>`。现在脚本按服务下发 `targetSchemaFolderId`（`APIFOX_SCHEMA_FOLDER_SPRING/GOZERO/NESTJS/FASTAPI`，未配置时回退 `APIFOX_SCHEMA_FOLDER_ID`），全量对齐只清理本服务目录内的模型；开启全量对齐却有服务没配模型目录时，脚本直接告警并给出 `apifox folder create --project <项目ID> --type schema --name <服务名>` 的修复命令
- **同步后自检并自动修复断链**：导入结束后导出一次项目快照（`apifox export --format apifox`），由 `scripts/apifox-schema-refs.py` 比对接口里 `#/definitions/<模型ID>` 与 `apifox schema list` 的现存模型，统计断链；命中时对本轮服务按 `OVERWRITE_EXISTING` 重导一次重新绑定，再复核一遍，仍有残留才报错退出（`APIFOX_VERIFY_SCHEMA_REFS=false` 可关闭自检）
- **只读检查入口 `./mix apifox-check`**：不改代码、只确认远端引用状态时用它（`--keep <目录>` 保留快照、`--examples <n>` 调整示例条数、`--no-color` 关彩色），输出「接口 N 个，数据模型 M 个」并逐条列出断链位置，退出码 0 完整 / 1 断链 / 2 缺配置或依赖。它需要联网与 `.env` 令牌，因此**不并入离线的 `./mix lint`**
- **责任人只补新增接口**：脚本先用一次 `apifox endpoint list` 取现有接口清单（`method path`），与产物求差集后只给新增接口注入扩展。原因是 Apifox 对「无差异导入」按不变处理（本地实测 `新增 0 / 更新 0 / 忽略 0 / 失败 0`），而每轮给全部接口重写扩展会让所有接口都被判定为已修改（修改时间与变更历史被刷新）；稳态下导入的就是原文档，计数全 0。要整体重写责任人时置 `APIFOX_MAINTAINER_FORCE=true`（此时退回逐接口全量注入）
- 该扩展会被 Apifox 保留在接口 `oasExtensions` 里并在文档页多渲染一行 `x-apifox-maintainer`，**只有真的注入过**才会再导入一次不带扩展的原文档把它清掉（`APIFOX_MAINTAINER_CLEAN_EXTENSION=false` 可保留，此时按全量注入以保证每轮导入内容与 Apifox 现存一致），责任人字段不受影响
- 令牌等同账号密码，脚本输出不回显令牌，根目录 `.env` 已被 `.gitignore` 忽略
- `./mix apifox` 现在一次做完两件事：接口走开放 API 导入，README 走 Apifox CLI（`doc create` / `doc update`）写入 `APIFOX_README_DOC_ID` 指定的项目 Markdown 文档；README 目标未配置或未装 CLI 时该步骤跳过并提示，不影响接口导入。`--no-readme` 只同步接口，`--create-readme` 首次创建 README 文档，单独同步用 `./mix apifox-readme`
- **WebSocket 接口走独立通道**：Apifox CLI 有 `websocket list/get/create/update/delete` 命令族（顶层 `--help` 不列出，由 `cli-schema list` 的 `websocket-create` / `websocket-update` 暴露），与 HTTP 接口的 `import-openapi` 互不影响。`apifox-sync.sh` 对 gozero 额外执行一步：读 `gozero/app/docs/websocket.json` → `websocket list` 按 `path` 匹配接口 ID → `websocket get` 取完整资源 → 只覆盖 `description` 与 `tags` → `cli-schema validate websocket-update` 校验 → `websocket update`
- WebSocket 同步**不碰** `name`、`parameters`、`commonParameters`、`folderId`、`moduleId`：这些由 Apifox 侧手工维护（浏览器 WebSocket 无法自定义请求头，`token` 是以 query 参数手工补的）。`websocket-update` 的 `additionalProperties` 为 false 且不是 JSON Patch，必须提交完整结构，所以脚本先 `get` 再在完整结构上替换，并剔除 `id` / `projectId` / `createdAt` 等只读字段，否则结构校验失败
- WebSocket 接口在 Apifox 中**不存在时只提示不创建**（首次仍需手工建一次，之后描述与标签变更会自动同步）；该步骤依赖 Apifox CLI 与 python，任一缺失时跳过并提示，不影响 HTTP 接口同步

### 接口描述写在代码声明处

产物内容由代码里的注解 / 装饰器决定，新增接口时同步补上，否则文档里只有路径没有说明（注解字符串一律写字面量，按通用规则 5 不抽常量）：

- 响应结构也必须在代码声明中保持可发现：NestJS 控制器为统一响应补充 `ApiResponseModel` 或重定向响应装饰器，FastAPI 路由为统一响应补充 `ApiResponse[T]` 泛型参数。修改后重新生成对应服务的 `docs/openapi.json` 与 `docs/openapi.yaml`，检查响应的 `data` schema 与实际返回值一致。
- Spring：`@Operation(summary, description)`、`@Tag`
- NestJS：`@ApiOperation({ summary, description })`、`@ApiTags`
- FastAPI：`@router.get/post(..., summary=, description=)`
- GoZero：`.api` 中的 `@doc(summary, description)`；handler 的 `ApplyApiLog` 描述不能留 `constants.API_LOG_PENDING_DESCRIPTION` 占位，必须换成 `app/common/constants/messages.go` 里具体的 `API_LOG_*` 文案

## 验证命令

统一入口是 `./mix compile <service>`（只编译校验，不产出打包目录）；下表列出各服务等价或更细的底层命令，编译未通过不得交付。

| 服务    | 验证                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| spring  | `./mix compile spring`（`mvn -q -DskipTests -Dspotless.check.skip=true compile`；打包 `mvn clean package -DskipTests`）             |
| nestjs  | `./mix compile nestjs`（`tsc --noEmit -p tsconfig.build.json`；打包 `npm run node:build`）                                          |
| fastapi | `./mix compile fastapi`（逐文件字节码编译，只报语法错误、不写 `__pycache__`；另有 pytest）                                          |
| gozero  | `cd gozero/app && GOTOOLCHAIN=local go build ./... && go vet ./... && go test ./... -count=1`；格式与静态检查走 `./mix lint gozero` |
| gateway | `apisix.yaml` 改动后校验 YAML 语法与目标路由的插件挂载（配置驱动，无业务代码）                                                      |

FastAPI 的编译校验刻意不用 Pyright：仓库既有类型基线存在大量报错（主要在测试文件），作为门禁会一直失败；`pyright` 仍保留在 `fastapi/pyproject.toml` 供编辑器使用。`./mix compile` 对未安装工具的服务返回码 2 并跳过，不能把「跳过」当成「通过」。

**Windows 主机上，fastapi 的 `./mix compile fastapi` 与 `./mix test fastapi` 不要用 WSL 的 bash 执行（仅 Windows + WSL 场景，Linux/macOS 按默认命令即可）**：底层是 `uv run`，WSL 里的 Linux uv 会清空并重建 Windows 创建的 `fastapi/.venv`（机制与处置见「仓库工程约束」的依赖环境条目）。这两步在 Windows 上只在 Git Bash / PowerShell 里跑，或改用 `fastapi/.venv/Scripts/python.exe` 的只读等价命令。

### 单元测试与测试工具

各服务的测试工具与运行入口固定，不要引入第二套测试框架；测试分层、必测矩阵与编写规则见 `references/unit-testing.md`：

| 服务    | 测试工具                                                                                        | 命令                                                             |
| ------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| spring  | JUnit 5（Jupiter）+ Mockito + AssertJ；响应式链用 `StepVerifier`，Controller 用 `WebTestClient` | `./mix test spring`（`cd spring && mvn test`）                   |
| nestjs  | Jest + ts-jest（配置在 `nestjs/package.json` 的 `jest` 段）                                     | `./mix test nestjs`（`bun run test -- --runInBand`）             |
| fastapi | pytest，异步用例用 anyio 插件的 `@pytest.mark.anyio`                                            | `./mix test fastapi`（`cd fastapi && uv run pytest -q`）         |
| gozero  | Go 标准库 `testing` + `net/http/httptest`，断言可用 testify `assert`（未引入 mock / suite / sqlmock） | `./mix test gozero`（`cd gozero/app && go test ./... -count=1`） |
| gateway | 无单元测试（配置驱动，不参与）                                                                  | `./mix test gateway` 直接跳过                                    |

工具未安装时该服务返回码 2 并跳过，「跳过」不能当成「通过」；只要改动了服务代码或测试，`./mix test <service>` 就是交付前必跑项（顺序见下一节）。

**NestJS 的 spec 必须同时能被 Jest 与 `bun test` 执行**：`./mix test nestjs` 与 `bun run test` 走的是 Jest（仓库基线，用 `ts-jest` 转换），而 `bun test` 走的是 Bun 内置 `bun:test` 与一层 `jest` 兼容层，两者 API 并不完全对齐。因此 spec 只使用两者都提供的 API（`jest.mock`、`jest.fn`、`jest.spyOn`、`jest.restoreAllMocks` 与 `expect.*`），**禁止 `jest.requireActual`、`jest.requireMock`、`jest.unmock`、`jest.deepUnmock`**，也禁止 `import ... from "bun:test"` 或为兼容新增双导出层，仓库不维护两套测试入口。mock 系统边界（如 `node:http`）时在工厂里显式返回被测代码真正用到的成员即可。报错 `TypeError: jest.requireActual is not a function` 表示用 `bun test` 跑到了含 Jest 专有 API 的 spec，修改 spec 而不是换运行器。

### 代码风格检查与格式化

生成或修改代码后，先格式化再检查，两者都通过才算完成。省略服务名时处理 spring、gozero、nestjs、fastapi 全部：

```bash
# Spring：Eclipse formatter + import 四段分组，配置在 spring/eclipse-formatter.xml
# lint 额外执行 scripts/controller-vo.py（控制器是否返回匿名 Map）与 scripts/constants.py（常量注释与分类）
./mix format spring      # mvn spotless:apply
./mix lint spring        # mvn spotless:check + 控制器返回类型检查 + 常量规范检查

# GoZero：Go 配置在 gozero/app/.golangci.yml，.api 文件用 goctl api format
./mix format gozero      # golangci-lint fmt + goctl api format
./mix lint gozero        # 常量规范检查 + golangci-lint run + .api 格式检查（临时目录格式化后 diff）

# NestJS：配置在 nestjs/.prettierrc 与 nestjs/eslint.config.mjs
./mix format nestjs      # npm run format + npm run lint:fix
./mix lint nestjs        # npm run lint + npm run format:check + 常量规范检查

# FastAPI：配置在 fastapi/pyproject.toml
./mix format fastapi     # ruff format . + ruff check --fix .
./mix lint fastapi       # ruff check . + 常量规范检查
```

底层脚本是 `scripts/format.sh` 与 `scripts/lint.sh`，对应工具未安装时该服务会自动跳过并提示；`gateway` 为 APISIX 配置，不参与。行尾由根目录 `.gitattributes` 统一为 LF。

### 交付前校验顺序

改完代码后按固定顺序自检，任一步未通过都不算完成（各步命令与底层实现见「验证命令」与「代码风格检查与格式化」章节）：

```bash
./mix format <service>    # 1. 自动格式化
./mix lint <service>      # 2. 代码检查
./mix compile <service>   # 3. 编译校验（只编译，不打包）
./mix test <service>      # 4. 单元测试
```

Windows 主机上执行第 3、4 步时，fastapi 必须在 Git Bash / PowerShell 里跑（WSL bash 中的 `uv run` 会重建 `.venv`，此项只影响 Windows + WSL，Linux/macOS 不受影响）；用不带服务名的 `./mix compile` / `./mix test` 会连带 fastapi，同样要在 Windows 侧 shell 执行，或把 fastapi 换成 `fastapi/.venv/Scripts/python.exe` 的只读等价命令

### Git 提交钩子

仓库内置版本化钩子，启用后**默认只有 pull 时的技能同步生效，提交检查默认关闭**，需要时单独开启：

```bash
./mix hooks                        # 启用（git config core.hooksPath .githooks）
./mix hooks status                 # 查看 hooksPath 与两项能力的开闭状态
./mix hooks enable commit          # 开启提交检查：格式化 → 检查 → 编译校验 → 单元测试，失败即阻止提交
./mix hooks disable commit         # 关闭提交检查（默认状态）
./mix hooks disable skills         # 关闭 pull 后的技能同步（默认开启）
./mix hooks uninstall              # 停用全部（清除 core.hooksPath）
```

- 两项能力独立开关，都存本仓库 git config：提交检查 `mix.hooks.commit`（**默认关闭**，只有显式 `true`/`1`/`yes`/`on` 才执行）、技能同步 `mix.hooks.skills`（**默认开启**，写 `false`/`0`/`no`/`off` 才关闭）；`enable`/`disable` 支持 `commit`、`skills`、`all`

- 钩子只对暂存区里属于 `spring/`、`gozero/`、`nestjs/`、`fastapi/` 的改动生效；非这四个目录的提交（文档、`scripts/`、`gateway/`）直接放行
- 格式化跑完后会把结果重新 `git add -u` 进暂存区，保证提交的是格式化后的版本
- 拉取联动：`.githooks/post-merge` 在普通 `git pull`（merge）完成后执行 `./mix skills`；`git pull --rebase` 不触发 `post-merge`，由 `.githooks/post-rewrite` 复用同一段逻辑。同步脚本幂等（内容一致时跳过），失败只提示、不影响 pull 结果
- **Windows 下必须在 Git Bash 里执行 pull**：WSL 的 bash 里 `HOME` 指向 Linux 侧主目录，`./mix skills` 会同步到 `/home/<user>` 而 IDE 读的是 `C:\Users\<user>`，看起来成功但技能没更新
- 临时跳过单次提交或拉取：`SKIP_HOOKS=1 git commit ...`、`SKIP_HOOKS=1 git pull ...` 或 `git commit --no-verify`
- 钩子是 bash 脚本，由 Git 自带的 `sh` 执行：Linux/macOS 直接可用，Windows 走 Git for Windows 自带的 Git Bash（无需 PowerShell 版本）；换行符由 `.gitattributes` 统一为 LF
- 新克隆的仓库需执行一次 `./mix hooks` 才会启用；生成代码时不要依赖钩子替代手动校验，钩子有跨服务共享脚本的覆盖缺口（改 `scripts/` 下的检查脚本本身不会触发服务检查）

`mix` 脚本顶层子命令新增 `compile` 与 `hooks`，完整列表见「仓库工程约束」章节。
