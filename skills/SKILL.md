---
name: mix-web-demo
description: mix-web-demo 多语言微服务仓库专属编码规范，覆盖 Spring WebFlux、NestJS、FastAPI、GoZero 四个服务与 APISIX 网关的分层组织、依赖注入、请求校验、实时链路、日志、测试、常量、并行化、SQL 参数化、远程调用、Swagger 生成与 Apifox 同步约定，并含仓库工程约束（行尾、goctl 生成流程）。在本仓库生成或修改任何服务代码时必须使用；与通用 skills 冲突时以本 skill 的项目实证约定为准。
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
5. 常量抽取：四个服务均有常量类，消息类字符串必须进常量类引用
   - Spring：`common/constants/Messages.java`、`HttpCode.java`
   - NestJS：`common/constants/`（`Messages`、`HttpCode`、`Defaults`、`ErrorIds`）
   - FastAPI：`core/constants/`（`Messages`、`HttpCode`、`RedisKeys`、`Scripts`、`WarehouseScripts`）
   - GoZero：`app/common/constants/`（`messages.go`、`defaults.go`）
   - 语言支持字符串模板时（Python f-string、TS 模板串、Go fmt），动态部分用模板拼接常量，不把整句抽离
   - 注解 / 装饰器的字符串参数**不抽常量**，直接写字面量：这类字符串只在声明处使用一次，抽到常量类后需跳转查看，反而降低可读性
     - Spring：`@Operation(summary, description)`、`@Tag`
     - NestJS：`@ApiOperation({ summary, description })`、`@ApiTags`
     - FastAPI：`@router.get/post(..., summary=, description=)`
     - GoZero 无注解机制，不适用本条
6. 相互独立的 IO 调用（RPC/HTTP/DB/Redis/ES/MQ）必须并行化，禁止串行等待；各服务并行原语见对应章节
7. 日志遵循各服务现有封装（见各服务章节），禁止绕过封装直接 print/console/logx 散用
8. 远程调用统一走各服务封装的客户端，自动透传用户上下文头：`X-User-Id`、`X-Username`、`X-Session-Id`、`Authorization`、`X-Internal-Token`；无登录用户时内部令牌 `userId=-1` 表示系统调用。禁止在新代码里裸用 httpx/axios/WebClient/http.Client 直连其他服务。各服务的唯一入口与底层 HTTP 客户端：
   - Spring：`infra/client/ServiceWebClient`（**WebClient** + `@LoadBalanced` 按服务名寻址 + Resilience4j 熔断/重试），按目标服务加方法
   - GoZero：`app/common/client` 的 `ServiceDiscovery.CallService`（**go-zero `rest/httpc`** + Nacos 轮询 + 退避重试），按目标服务在 `internal/client/` 封装
   - NestJS：`module/common/nacos/nacos.service.ts` 的 `call(opts)`（**axios** + axios-retry + opossum），按目标服务在调用方封装 Client 类
   - FastAPI：`app/core/client/client.py` 的 `call_remote_service`（**httpx** 共享连接池 + SimpleCircuitBreaker + tenacity），按服务在 `internal/clients/` 封装
9. **HTTP 连接池必须随服务生命周期释放**，不能指望进程退出收尾。现状与要求：
   - FastAPI 已规范：两个 `httpx.AsyncClient`（内网 `trust_env=False` 与外部抓取各一个）由 `lifespan` 创建、`yield` 之后 `aclose()`，**新增长连接客户端必须走同一处创建与释放**
   - Spring 由容器管理 reactor-netty 全局连接池，无需手工关闭；但禁止在请求路径上反复 `WebClient.builder().build()`，应注入 `WebClient.Builder` 并缓存实例
   - GoZero 已收口为单条链路：`ServiceDiscovery.Close()` → 三个业务 Client 的 `Close()` → `ClientContext.Close()` → `ServiceContext.Close()`，新增客户端必须接进来
   - NestJS 已收口：`NacosService` 实现 `OnModuleDestroy`，注销 Nacos 实例 + `shutdown()` 熔断器 + `destroy()` 专用 agent；新增持有的连接资源挂同一处，不要另建包级 stop 函数
10. 服务发现基于 Nacos；新服务接入需注册实例并在 metadata 声明能力
11. 生成代码时参考目标服务同类文件的命名与组织方式；已有成熟风格优先
12. 注释说明：注释的结束不能包含中文句号，直接留空，如果注释过长，使用多行注释形式，而不是多条单行注释，短注释使用1行的单行注释即可
   - 新增或修改的代码注释、装饰器说明和文档说明均不得以中文句号 `。` 结尾，统一以无句号文本或其他必要标点结束
13. **日志采集必须排除敏感字段**：请求体进入日志后会被投递到 `api-log-queue`，最终落在 MongoDB `apilogs` 与 ClickHouse `ods_api_log`，因此凡是携带密码、验证码、令牌、授权码的接口都要显式排除。各服务能力：Spring `@ApiLog(excludeFields = {...})`、NestJS `@ApiLog({ excludeFields: [...] })`、FastAPI `@logWithConfig(exclude_fields = [...])`（`@log` 不支持）；**GoZero 的 `ApplyApiLog` 没有任何排除能力**，涉及凭据的接口不要挂它，或先给中间件补过滤参数
14. **新增接口必须带参数校验**，任何接收请求参数的接口都要声明校验规则，不得只靠业务层兜底。各服务写法见对应章节；**GoZero 的校验标签写在 `.api` 文件里**（随 goctl 生成进 `types.go`），漏写标签等于该参数没有校验，不会报错也不会告警
15. **新增、修改或删除对外接口后，必须重新生成静态 OpenAPI 文档并同步 Apifox**：先 `./mix swag <service>`，产物（`openapi.json` + `openapi.yaml`）与服务代码同一次提交；再 `./mix apifox <service>` 同步到 Apifox，未配置令牌时跳过并说明。完整流程见「接口文档收尾流程」章节

## Spring 服务（spring/，WebFlux 响应式栈）

### 目录组织（三层 + 横切）

```
api/controller   接口层（返回 Mono/Flux）
api/service      业务接口
api/service/impl 业务实现
api/repository   R2DBC Repository
entity/po|vo|dto|projection  实体与视图对象
entity/assembler 实体到 VO 的装配器（依赖 api/repository，供 service/impl 复用，跨包调用需 public）
infra/client     远程调用客户端（ServiceWebClient）
infra/filter     WebFilter（UserContextWebFilter）
infra/handler    全局异常处理（GlobalExceptionHandler）
core/config|aspect|annotation|properties  配置、切面、注解、属性
common/constants|utils  常量与工具（RedisUtil、JwtUtil、UserContext）
```

### 硬性约定

- **依赖方向**：`api` 是最上层，`infra` / `core` / `common` / `entity` 都不依赖它；目前唯一例外是 `entity/assembler`（装配器需要 `api/repository` 才能加载关联数据）。新增跨层组件前先确认会不会引入新的反向依赖
- ORM 是 Spring Data R2DBC，不是 MyBatisPlus：Repository 继承 `ReactiveCrudRepository<T, ID>`；自定义 SQL 用 `@Query` + `:param`，更新加 `@Modifying`；事务用 `TransactionalOperator.transactional()` 包裹，禁止 `@Transactional`
- Controller 返回 `Mono<Result<T>>` / `Flux<Result<T>>`，Service 返回 `Mono<T>` / `Flux<T>`；禁止返回裸类型、禁止调用 `.block()`
- 请求上下文走 Reactor Context：`UserContextWebFilter` 用 `.contextWrite()` 写入，业务用 `Mono.deferContextual(ctx -> ...)` 读取 `UserContext.getUserId(ctx)`；禁止 `ThreadLocal`、`RequestContextHolder`、`OncePerRequestFilter`、`HandlerInterceptor`
- 并行独立 IO 用 `Mono.zip()` / `Mono.when()`，禁止 `CompletableFuture.allOf()`
- 阻塞操作（加密、验证码图片等）用 `Mono.fromCallable(() -> ...).subscribeOn(Schedulers.boundedElastic())` 隔离
- 全局异常：`@RestControllerAdvice` + `@ExceptionHandler` 返回 `Mono<ResponseEntity<Result<?>>>`，通过 ResponseEntity 设置 HTTP 状态码；`ResponseBodyAdvice` 在 WebFlux 不可用
- **WebFlux 的请求体校验失败抛的是 `WebExchangeBindException`（继承 `ServerWebInputException`），不是 MVC 的 `MethodArgumentNotValidException` / `org.springframework.validation.BindException`**。`@ExceptionHandler` 未声明它就会被 `@ExceptionHandler(Exception.class)` 兜底吞成 500，必须显式声明；畸形 JSON 与参数类型不匹配抛 `ServerWebInputException`，一并声明。字段消息取 `getBindingResult().getFieldError().getDefaultMessage()`
- **请求 DTO 用 jakarta 注解声明约束（放 `entity/dto/`），控制器参数用 `@Valid` 触发**；新增接口必须带校验（通用规则 13），只有 `@RequestParam` / `@PathVariable` 这类无 DTO 的入参属于例外，那种情况控制器**没有**类级 `@Validated`，需要在 service 层手工校验
- 微服务调用用 `ServiceWebClient`（WebClient + `@LoadBalanced` 服务名寻址 + Resilience4j 熔断/重试），新增远程接口在该类中加方法，通过 `deferContextual` 注入上下文头；禁止 OpenFeign。**当前实现在每次请求里 `webClientBuilder.build()` 重建 WebClient**：连接池是 reactor-netty 全局的所以不会泄漏，但每次构建有额外开销，改造时应在 `@PostConstruct` 缓存一个实例（`WebClient` 不可变且线程安全）
- Redis 用 `ReactiveStringRedisTemplate`，封装在 `common/utils/RedisUtil`；缓存读写走 Mono 链式 `switchIfEmpty(Mono.defer(...))` 模式，禁止 `@Cacheable`
- AOP 切面中 `pjp.proceed()` 返回 `Mono<?>` 时必须在 Mono 链内操作（`.flatMap()` / `.doOnSuccess()`），上下文用 `.deferContextual()` 获取
- 横切能力由 AOP 实现：`ApiLogAspect`（接口日志）、`PermissionValidationAspect`（`@RequirePermission` 声明式权限）、`InternalTokenAspect`（`@RequireInternalToken` 内部令牌）、`ArticleSyncAspect`（文章变更同步 MQ / ES / 向量）、`Neo4jSyncAspect`（图谱同步）。新增写接口时确认是否需要权限注解与同步触发，同步失败只记日志、没有补偿机制
- **响应式切面的固定写法**：`pjp.proceed()` 返回的是**未订阅的冷流**（业务代码此时尚未执行），且 Reactor Context 只在订阅时可见。所以切面必须把校验 / 日志 / 同步挂到 Mono 链上（`Mono.deferContextual(ctx -> ...)`）：校验类用 `validate(ctx).then(businessMono)` 保证「校验先于业务」，副作用类用 `monoResult.doOnSuccess(...)` 发后即忘；副作用里若需要用户身份，必须用 `UserContext.writeContext(Context.empty(), ...)` 重建 Context 再 `contextWrite`，否则异步链上读不到。**禁止用同步代码在 `proceed()` 之前读上下文**，那时 ctx 不可见，只会拿到 null
- 注入风格：`@Service` + `@RequiredArgsConstructor` + `private final` 字段（构造器注入），禁止字段 `@Autowired`
- Swagger 用 springdoc：`@Operation(summary, description)`、`@Tag`，注解参数直接写字面量，不抽常量
- 日志：`common/utils/SimpleLogger` 实例注入使用

## NestJS 服务（nestjs/，Fastify + Mongoose/TypeORM）

### 目录组织

```
config/           YAML 配置与 index.ts 加载器
common/constants  常量（Messages、HttpCode、Defaults、ErrorIds）
common/exceptions 全局异常与错误结构
common/utils      工具类
framework/        全局横切：decorators、guards、interceptors、filters、middleware
module/common/    公共服务模块（nacos、logger、oss、redis、mail、github、task、client）
module/system/    系统业务模块（apiLog、articleLog、sqlTools 等）
```

### 模块内组织与约定

- 每个业务模块：`xxx.module.ts` + `xxx.controller.ts` + `xxx.service.ts`，辅以 `dto/` 与 `schema/`（Mongoose）或 `entities/`（TypeORM）
- ORM 按模块现状选择：日志类用 Mongoose（`@Schema` + `SchemaFactory`，`@InjectModel`）；结构化表用 TypeORM（`@InjectRepository`）。新模块先参考同类模块，禁止凭空引入新 ORM
- **入参校验走全局 `ValidationPipe`（`app/index.ts` 注册，`transform` + `enableImplicitConversion`），DTO 用 class-validator 注解**；新增接口必须带校验（通用规则 13），每个 `@Body()` / `@Query()` / `@Param()` 都要有对应 DTO 与约束注解，直接用裸参数接请求等于没有校验。自定义 `exceptionFactory` 把错误包成 `BusinessException(400, PARAM_PARSE_FAILED)`，最终由 `AllExceptionsFilter` 输出统一结构。**当前未开 `whitelist` / `forbidNonWhitelisted`**，未声明字段既不剥离也不报错，不要依赖"多余字段会被拒"
- 请求上下文用 nestjs-cls：`ClsMiddleware` 写入（userId/username/sessionId/token/internalToken），业务注入 `ClsService` 读取；gRPC 或脱离 HTTP 异步链的场景必须用 `ClsService.run` 手动开启上下文
  - **未登录语义注意**：`parseUserId` 要求 `Number.isInteger(userId) && userId > 0`，所以 ≤0 的值（含约定的系统调用 `-1`）在 CLS 里是 `undefined`；出站头由 `NacosService.call` 生成（`X-User-Id: String(userId || 0)`，内部令牌按 `userId > 0 ? userId : -1`）。需要区分"未登录 / 系统调用"时不要直接依赖 CLS 的值
- 公共层入口是 `module/common/common.module.ts`：`imports` 只保留需要根级加载的子模块（Logger、Client、Github、Mail、Task），`exports` **只导出 ClientModule**（根模块的 `RequireAdminGuard` 需要它）。业务模块用到的其他公共能力（oss、word、nacos、redis）由消费方**自行 import 对应模块**，禁止把 CommonModule 做成"全量中转池"（那会让模块边界形同虚设）
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
- **响应 Schema 必须统一抽离**：业务响应的 `SchemaObject`（包括分页、同步、统计、上传和查询结果）统一定义在 `common/utils/swaggerResponse.ts`，控制器中的 `@ApiResponseModel` 只引用命名常量，禁止在控制器内重复编写内联 `data: { ... }`。除 `data: null` 外，必须为实际字段、数组项和嵌套对象补充 `description`；不能用无字段的 `SwaggerObjectData` 代替已知结构。
- **路径和查询参数命名必须与实际 URL 一致**：本项目 OpenAPI 会将字段转换为 snake_case。路径参数统一使用 snake_case，并让路由、`@Param`、`@ApiParam` 三处名称完全一致，例如 `:user_id` + `@Param("user_id")`、`:table_key` + `@Param("table_key")`。查询参数也必须统一，例如 `custom_filename` + `@Query("custom_filename")`，禁止同时出现 camelCase 与 snake_case。
- **Swagger 参数重复检查**：修改接口后重新生成 OpenAPI，检查每个 operation 的 `parameters` 是否存在重复语义或同时存在大小写不同的参数；重点排查 `userId/user_id`、`tableKey/table_key`、`customFilename/custom_filename` 等组合。
- 日志：注入 `LoggerService`（`module/common/logger`）

## FastAPI 服务（fastapi/）

### 目录组织

```
app/core/         基础设施：auth、base(Logger)、client(远程调用)、config、constants、db、errors
app/common/       decorators、middleware（contextvars 上下文中间件）
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
- `__init__.py` 导出：包内有 `__init__.py` 导出的功能，导入一律走包路径（`from app.internal.crud import UserAnalysisMapper`），禁止深入到文件路径；新增模块必须同步更新 `__init__.py` 导出
- 类型标注全覆盖；`import` 全部在文件顶部，禁止逻辑中导入；生成后检查并删除未使用的 import
- **入参校验用 Pydantic 模型**（放 `internal/schemas/`，文件名 `xxxDTO.py`）：字段用 `Field(...)` 声明，单字段规则用 `@field_validator` + `PydanticCustomError`（中文消息，参考 `createHistoryDTO.py`），请求体禁止用裸 `dict` / `Any` 接收；新增接口必须带校验（通用规则 13）
- **统一响应模型使用泛型**：`core/base/response.py` 的 `ApiResponse[T]` 负责声明 `code`、`msg` 和 `data`，路由必须通过 `response_model=ApiResponse[具体类型]` 暴露返回结构。已知结构使用领域 DTO、列表或字典泛型；只有运行时结构确实不固定时才使用 `ApiResponse[object]`，禁止退回不带类型参数的 `ApiResponse`
- **FastAPI 响应结构必须可展开**：已知返回字段必须定义 Pydantic 响应 DTO，并在路由使用 `response_model=ApiResponse[具体 DTO]`；禁止用 `ApiResponse[object]` 隐藏可确定的 `data` 结构。DTO 的每个字段、嵌套对象和列表项都要用 `Field(description=...)` 写明含义。
- SQL：ClickHouse 查询用 `%(name)s` 参数化；SQL 模板集中在 `core/constants/scripts.py` 与 `warehouse.py`，业务代码不内联 SQL 字符串
- 缓存：使用 `internal/cache` 的两级缓存体系（L1 内存 5 分钟 + L2 Redis 1 天 + ClickHouse 版本号失效），新统计接口优先接入而非自造缓存
- 定时任务：APScheduler 注册在 `internal/tasks/scheduler.py`，任务逻辑放 `tasks/logic/`；多实例互斥用 Redis `try_lock`/`unlock`（key 进 `RedisKeys` 常量）
- 远程调用：统一 `core/client/call_remote_service`（httpx 共享连接池 + SimpleCircuitBreaker 熔断 + tenacity 重试 + 上下文头自动注入），按服务在 `internal/clients/` 封装 Client 类。两个共享 `AsyncClient`（内网 `trust_env=False`、外部抓取走系统代理）在 `lifespan.py` 创建、`yield` 之后 `aclose()` 释放，**新增客户端必须走同一处创建与释放**，不要另建模块级客户端
- ClickHouse ORM 会话的唯一入口是 `core/db/clickhouse.py` 的 `clickhouse_session()`（`get_clickhouse_db` 复用它）。**粒度保持"每查询一个会话"**：`crud/user.py` 有 `asyncio.gather` 并发跑两条 CH 查询，而 `AsyncSession` 不支持并发复用；非请求链路用引擎级 `execute_clickhouse_query` / `execute_clickhouse_sql`
- Agent 工具经 `internal/agents/toolFactories.py` 的 `AgentToolFactories` 注入 `BaseAiService`（**传工厂而非实例**，以保留线程池并行加载与单组失败隔离）
- Agent 工具权限：`internal/agents/toolScope.py` 的 contextvars 作用域（**fail-closed**）——`intentRouter` 在路由前统一写入 `ToolScope(user_id, is_admin)`，SQL 与 MongoDB 工具执行前校验行级范围（查询必须含 `user_id` 且绑定值等于当前用户，admin 放行）。禁止把请求态写进 `@lru_cache` 单例的实例字段
- 日志：`from app.core.base import Logger`，`Logger.info/warning/error/debug`
- 上下文：`common/middleware/contextMiddleware.py` 的 contextvars（`get_current_user_id` 等），深层函数免参读取用户信息

## GoZero 服务（gozero/，API-First）

### API-First 流程（强制）

1. 先在 `gozero/api/` 修改 `.api` 文件：`main.api` 按业务分组 import（chat、search、sqlTools、task 等），路由写在分组文件中，`@server` 块声明 `group`、`prefix`、`middleware`
2. 生成代码：`gozero/script/goctl/genApi.sh`（bash）或 `genApi.ps1`（PowerShell），两者等价，顶层入口 `scripts/goctl-api-init.sh`。核心动作是 `goctl api format -dir .` + `goctl api go -api main.api -dir ../app --style=goZero --home ../template`；脚本会自动备份并还原 `main.go` 与 `etc/`、删除生成的 `app.go`
3. ORM：`gozero/script/goctl/genOrm.sh` / `genOrm.ps1`（`goctl model mysql ddl --style goZero --home ../template`），SQL DDL 放 `gozero/script/sql/`
4. 模板在 `gozero/template/`（api、model、mongo、newapi 等），生成代码基于模板；禁止手写 handler/types 绕过生成流程，logic 文件头部有 `// Code scaffolded by goctl. Safe to edit.` 标记可编辑
5. **生成后必须处理的四件事**：
   - `goctl` 会把 `.api`、`types.go`、`routes.go` 的行尾统一转成 LF，仓库约定 CRLF，需逐文件转回
   - import 路径若发生变更，import 块的字母序会失效（`gofmt -l` 会报未格式化），按「剥离 CRLF → gofmt 重排 → 还原 CRLF」处理
   - 已存在的 handler / logic 会被跳过（`exists, ignored generation`），**模板改动不会回灌到已有文件**：`template/api/handler.tpl` 里的 `ApplyApiLog(..., "TODO: 添加接口描述")` 是占位字面量（存量 handler 都手工换成了 `constants.API_LOG_*`），所以「重新生成」只对**缺失**文件安全，改了 `handler.tpl` 必须手工同步存量 handler
   - 生成后跑 `cd gozero/app && go build ./...` 确认模板不变量未被破坏

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
app/model/<table>        数据模型（goctl 生成 _gen.go + custom 扩展文件）
```

- **分层方向单向**：`internal/*` 可依赖 `common/*`，`common/*` **不得**依赖 `internal/*`。实时帧类型定义在 `.api` → `internal/types`，hub 因此放在 `internal/hub`；若放 `common/hub` 就会产生反向依赖
- logic 中禁止 SQL：数据访问全部封装在 `app/model/`，logic 通过 `l.svcCtx.XxxModel.Method(l.ctx, ...)` 调用；model 方法第一个参数是 `ctx`
- svc 分域：`ServiceContext` 匿名嵌入 `RuntimeContext`、`InfrastructureContext`、`ModelContext`、`HubContext`、`ClientContext`、`LoggerContext`、`MiddlewareContext`；新增依赖加入对应分域，在 `serviceComponentsContext.go` 组装，禁止往 ServiceContext 平铺字段
- **定时任务调度器挂在 `RuntimeContext.TaskScheduler`**（从包级变量收口）：`internal/task` 只提供 `NewTaskScheduler(svcCtx) *cron.Cron` 负责构造并启动，返回值由 `boot/server.go` 赋给 `ctx.TaskScheduler`；停止统一由 `ServiceContext.Close()` 承担（先 `TaskScheduler.Stop()` 再 `Cancel()`），`boot/init.go` 的关闭入口调 `ctx.Close()` 而非直接操作调度器。**不要再引入包级调度器变量**（测试无法替换、生命周期不受 Close 管理）。cron 表达式用标准 5 字段（分 时 日 月 周），"每小时"是 `0 * * * *`，写成 `* * */1 * *` 会变成每分钟执行
- `ServiceContext.Close()` 是唯一的关闭入口；新增需要释放的资源时把释放逻辑加进 `Close()`，不要另建包级 stop 函数
- 日志：logic 结构体嵌入 `*utils.ZeroLogger`（构造时 `ZeroLogger: svcCtx.Logger.WithContext(ctx)`），调用 `l.Info/l.Errorf/l.Error`；logx 全局方法仅限启动阶段（logx 无 Warn/Warnf）；项目 ZeroLogger 提供 `Warningf`，警告级日志用它，异常一律 `l.Errorf`
- 并行：`mr.Finish`，每个任务为 `func() error`，结果写入闭包局部变量，任务内部吞错返回 nil（错误在任务外统一处理）
- context：一切可能阻塞的函数第一个参数接收 `context.Context`，嵌套调用透传同一 ctx；logic 用 `l.ctx`
- 中间件：`.api` 文件 `@server middleware:` 声明 + `routes.go` 的 `rest.WithMiddlewares`；内部服务接口必须挂 `InternalServiceMiddleware`（校验 `X-Internal-Token`）
- 远程调用：统一走 `common/client` 的 `ServiceDiscovery.CallService(ctx, serviceName, path, RequestOptions)`，按目标服务在 `internal/client/` 封装 Client 结构体，logic 里禁止直接发 HTTP。发送层是 go-zero 的 `rest/httpc`，服务发现/负载均衡/重试/响应解析仍由自己实现，详见下面「远程调用（httpc）」小节
- 常量：消息进 `app/common/constants/messages.go`，动态部分 `fmt.Sprintf(constants.XXX+": %v", err)` 拼接
- 构建校验：`cd gozero/app && go build ./... && go vet ./... && go test ./... -count=1` 必须通过；**涉及依赖变动时加 `GOTOOLCHAIN=local` 复核**（对齐 Docker 的构建约束，避免 toolchain 自动升级掩盖版本漂移）；检查未使用导包与变量；产物命名与入口一致；格式用「剥离 CRLF → `gofmt -l`」复核，禁止直接 `gofmt -w`

### 请求参数校验

- **机制：go-playground/validator 标签式校验**。标签写在 `.api` 字段上，随 goctl 生成进 `internal/types/types.go`；**不再有手写的 `<domain>Validate.go`**，新增请求类型不需要补任何 Go 代码
- 生效链路：`boot.CreateServer` 调 `validation.InitValidator()` → `httpx.SetValidator` 注册 → `httpx.Parse` 在解析完 path/form/header/json 后触发校验。**请求类型绝不能实现 `Validate() error`**：`httpx.Parse` 是 `if 实现接口 { ... } else if 注册的校验器 != nil { ... }`，一旦实现了方法就会走前一个分支，让 `SetValidator` 静默失效（本项目早期踩过这个坑并回退过一次）
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
- 校验器是必需依赖：`InitValidator()` 失败直接 panic 拒绝启动；`internal/types/validate_test.go` 的 `TestHttpxParseRunsTagValidation` 专门守护「注册的校验器确实被 `httpx.Parse` 触发」这条链路，不要删

### 远程调用（httpc）

- 入口：`common/client` 的 `ServiceDiscovery.CallService`，按目标服务在 `internal/client/` 封装 Client 结构体，logic 里禁止直接发 HTTP
- **发送层用 go-zero 的 `rest/httpc`**：`sd.service(serviceName)` 按服务名缓存 `httpc.Service`（熔断器名与链路追踪都绑定服务名），构造用 `httpc.NewServiceWithClient(名, sd.httpClient, injectContextHeaders)`。**必须用 `NewServiceWithClient` 注入项目自己的 `http.Client`**，`httpc.NewService` 内部是 `http.DefaultClient`，没有超时
- **httpc 只接管「发出去」这一段**：按服务名的熔断、OpenTelemetry span 与 traceparent 注入、`[HTTP] 状态码 - 方法 URL` 耗时日志。Nacos 服务发现、轮询负载均衡、退避重试、`{code,msg,data}` 响应体解析仍由 `ServiceDiscovery` 自己实现
- `httpc.Do(ctx, method, url, data)` 的 `data` 走 `mapping.Marshal`，**只接受结构体**（字段带 `path`/`form`/`header`/`json` 标签），传 `map[string]any` 会直接 panic。所以发送走 `sd.service(name).DoRequest(req)`，请求体继续由 `buildRequestBody` 构造
- `httpc` **不把 5xx 当错误**（只给 `resp.StatusCode`），状态码判定与 `httpStatusError` 必须保留；响应解析继续用 `json.Unmarshal`，**不要换成 `httpc.Parse`**（它不支持 `any` / `json.RawMessage` 字段，`map[string]any` 还会把数字弱化成字符串）
- 上下文头与内部令牌在 httpc 的 `Option`（`injectContextHeaders`）里注入，从 `r.Context()` 读用户身份；请求头常量统一放 `common/constants/remoteCall.go`
- 熔断打开时 httpc 抢先返回 `breaker.ErrServiceUnavailable`：`CallService` 负责转成降级文案，`shouldRetry` 对该错误返回 false（重试无意义且会持续冲击熔断器）
- 熔断判定比早期更准：只有 **5xx / 超时 / 网络错误**计失败，4xx 与业务错误码不计
- **释放链路（2026-09-19 补齐）**：`httpc.Service` 不暴露底层 `http.Client`，所以在 `ServiceDiscovery` 上加了 `Close()`（内部 `httpClient.CloseIdleConnections()`）；三个业务 Client 各转发一个 `Close()`，由 `ClientContext.Close()` 汇总，最终挂在 `ServiceContext.Close()` 里。注意 `ClientContext.FastapiClient` 字段是业务契约接口（测试用 mock 实现），生命周期方法**不并入**该接口，用包内 `resourceCloser` 断言处理，新增客户端时保持这条链路
- 链路追踪：`core/trace` 在包 `init()` 里已设置 `TraceContext` propagator，`rest.MustNewServer` → `ServiceConf.SetUp()` 也会调 `trace.StartAgent`，所以**不配 `Telemetry` 也会注入 traceparent**，只是 span 不上报；接入采集端只需在 `etc/application.yaml` 加 `Telemetry: {Endpoint, Batcher}`
- 客户端可观测性：httpc 每次调用都会打一条 logx 日志（4xx/5xx 为 error 级），日志量会上升，这是换取链路可视化的代价

### 实时链路（SSE / WebSocket）

- **帧结构的单一来源是 `.api`**：`ChatSSEMessage`、`ChatWsMessage` 声明在 `api/chat/stream.api`，接口的 `returns` 直接指向它们，**不要**再建空的 `XxxConnectResp` 占位类型。goctl 生成类型用 `Id / UserId / SenderId / ReceiverId / MessageId` 命名，与手写结构旧的 `ID / UserID / ...` 不同，跨用时需改字段名并把 `uint` 改 `uint64`
- hub 与实时分发在 `internal/hub`（`chatHub`、`sseHub`、`chatRealtimeDispatcher`、`realtimeTypes`）：本机连接管理 + 跨 Pod 事件分发。内部信封 `ChatRealtimeEvent` 只在对内使用，**不进 `.api`**
- **不要采用 `sse_handler.tpl` 的「每请求 chan + handler 内 flush 循环」单机模式**：跨实例广播依赖 `internal/hub` + `common/pubsub/redisPubSub.go` 的 Redis Pub/Sub，照模板改会丢掉多副本下的消息投递。连接接管（`HandleConnection` / `upgrader.Upgrade`）必须留在 handler，且接管前不得写 `w`
- **`common/pubsub.RedisPubSub` 是「一个实例一个频道」**：频道在 `NewRedisPubSub(client, logger, channel)` 构造时绑定，`Publish` / `Start` 都不收频道参数。内部只持有单个 `*redis.PubSub` 引用，所以**同一个实例不能订阅第二个频道**（会覆盖前一个订阅的引用、造成连接泄漏与丢消息）。需要新频道就新建实例，频道常量统一放 `common/constants/redisKeys.go`
- 心跳与初始帧属协议内容：SSE 连接建立时下发 `{"type":"connected"}`，WS 收到 `{"type":"ping"}` 回 `{"type":"pong"}`

### 搜索链路

- 流程是「召回 → 融合重排 → 切页」：`resolveRecallWindow(page, size)` 把 `page * size` 按 `SEARCH_RECALL_STEP_SIZE`（100）向上取整成 `recallSize`，ES 以 `Page=1, Size=recallSize` 取一档候选；融合后由 `pageSlice` 在内存切出目标页，`total` 始终取 ES 的 `TotalHits`
- `page * size` 超过 `SEARCH_RECALL_MAX_SIZE`（200）时退化为窗口内重排并打 `SEARCH_RECALL_DEGRADE_LOG`
- 融合归一化分母取**整个召回候选集**的最大 ES 分（同一档位内各页可比）；未被向量或图谱召回的候选用**候选集均值**填充，权重保持全局固定。禁止把缺失信号的权重按比例重分配给其余信号
- 两层权重分开看：ES 内 `script_score` 权重（`ESScoreWeight` / `ViewsWeight` / `RecencyWeight` 等）管第一层，`FusionConfig`（`VectorScoreWeight` / `GraphScoreWeight` / `HybridMinESWeight`）管第二层
- ES 搜索脚本、权重、参数名映射三件套任一拉取失败 → 整条增强链路关闭，降级为普通 ES 条件分页查询（无脚本时补 `create_at` 降序，避免 `_score` 恒为 0 时顺序不确定）；ES 召回后回填 Spring 统计（views / likes / collects / follows）四路任一失败 → 该指标保留 ES 原值，不抛错
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
- `fix.py` 是生成后修补产物的固定环节，按顺序做四件事：
  - 补中文标签定义与 `info`（`tag_mapping`、`x-author`），并把每个 operation 的 `tags` 由英文替换为中文名
  - 移除 `swagger2openapi` 注入的全局 / path 级 / operation 级 `servers` 与 per-operation `schemes`（Swagger 2.0 文档没有 host，转换工具会默认补 `https://`，导致前端用错协议）
  - 剔除易变字段 `x-date`、`x-goctl-version`（`VOLATILE_FIELDS`），保证同一份 `.api` 在不同机器、不同 goctl 版本下生成结果可复现，不产生无意义 diff
  - 剔除 WebSocket 路径 `/ws/chat`（`WEBSOCKET_PATHS`）：Apifox 的 WebSocket 是独立于 HTTP 的资源类型，OpenAPI 无法表达、也没有对应扩展，导入只会多出一条无法发起握手的 GET 接口，该接口在 Apifox 侧手工维护；同时把 `/sse/chat` 的 200 响应改为 `text/event-stream`（复用 goctl 生成的 inline schema）并补 `400`
- GoZero 的 handler 模板会在运行时通过 `utils.Success/Error` 输出统一外壳 `{code,msg,data}`，而 `goctl api swagger` 只生成 `returns` 对应的 `data` schema；因此 `fix.py` 必须对 `application/json` 响应补齐该外壳，跳过 `text/event-stream`，并保持重复执行幂等。修改 `.api` 或响应模型后必须重新生成 JSON/YAML，检查响应 schema 的 `data` 是否仍为原始业务结构
- GoZero 的 `xxxResp` 按前端兼容规范保留业务 `Data` 字段并声明 `json:"data"`；handler 必须使用 `utils.Success(w, resp)`，由 `utils.Success` 识别并展开响应对象的 `Data` 字段，最终统一输出单层 `{code, msg, data}`，禁止产生 `data.data`。Swagger 后处理也必须同步展开该字段，保证文档与运行时响应一致。
- **该文档的 schema 全部是 inline（`components` 下没有 `schemas`），不要改成 `$ref`**
- 改完 `.api` 后按「接口文档收尾流程」重新生成并提交产物

## 网关（gateway/，Apache APISIX）

- 以 YAML 数据面运行（`role_data_plane` + `config_provider: yaml`），无业务代码；路由与插件全部在 `apisix/apisix.yaml`
- **认证外置**：业务路由挂 `forward-auth` 回调 Spring 的 `/users/internal/auth/validate`，由网关注入 `X-User-Id` / `X-Username` / `X-Session-Id` 供下游透传；**下游服务只信任请求头**，不自行解析 JWT
- 内部接口防护靠 `block-internal` 路由（URI 黑名单），新增内部接口必须同步加入黑名单
- **`block-internal` 的 `uri` 是精确匹配**（只有以 `*` 结尾才是前缀匹配），而它要挡的接口往往落在宽松前缀路由（`/articles/*`、`/users/*`、`/email/*`、`/ai_history/*`）覆盖范围内。新增内部接口时除了加黑名单，还要确认黑名单条目能覆盖实际访问路径，否则会出现「精确路径被挡、子路径可直达」的缺口
- 长连接用独立 upstream（读超时 3600s），与普通接口区分
- 新增对外路由：按既有分组挂 `forward-auth` 与 `limit-req`（登录类用 `*login_limit`）；public 路由必须有明确理由且不能漏挂限流
- 改配置后用 YAML 解析器校验语法，并确认目标路由的插件确实挂载
- **端口暴露**：根 `docker-compose.yml` 里只有 gateway 映射宿主机（8080 → 容器 9080），spring / gozero / nestjs / fastapi **均不映射宿主机端口**，容器间经 `hcsy` 网络 + Nacos 直连。下游无条件信任 `X-User-Id`，所以这个收敛状态正是身份不可伪造的前提，改动编排时不要给业务服务加回 `ports`；本地开发模式（`./mix dev seq`）直连服务端口，没有这层保护

## 仓库工程约束

- 行尾由根目录 `.gitattributes`（`* text=auto eol=lf`）统一为 LF，仓库不再按 CRLF 维护；新建文件不需要手工转换行尾
- 格式化统一走各服务的工具（`./mix format`）：Spring Spotless、GoZero golangci-lint、NestJS Prettier、FastAPI Ruff；不要再手工执行 `gofmt -w` 或 `prettier --write` 做全量重排
- Go 的格式问题用 `./mix lint gozero` 判断（golangci-lint 的 gofmt formatter），不要用裸 `gofmt -l`：它对行尾差异会报大量假阳性
- `goctl`（`api format` / `api go`）生成后跑 `./mix format gozero` 收敛格式即可，不需要再手工处理行尾
- **goctl 版本**：仓库已生成的 34 个文件头部标记 `goctl 1.9.2`，本机安装的如果是其他版本，重新生成会把版本注释刷成 对应版本（`types.go`、`routes.go` 一并刷新）。
- git 用于精确核对与回退：`git status --porcelain`、`git diff --ignore-cr-at-eol`（判断是否仅行尾差异）、`git checkout -- <文件>`
- 本机环境参考：Go / gofmt 在 `C:\Program Files\Go\bin\`，goctl 在 `C:\Users\30708\go\bin\goctl.EXE`，git 在 `C:\Program Files\Git\cmd\git.EXE`（`usr\bin\` 下有 grep / tr / sed / basename 等，用完整路径调用），maven 在 `C:\apache-maven-3.9.11\bin\mvn.CMD`，javap 在 `C:\Program Files\Java\jdk-17\bin\javap.exe`
- bash 环境的 `dirname` / `head` 等不稳定（PATH 时有时无），批量格式与行尾校验优先走 `./mix format` / `./mix lint`，需要脚本兜底时用 Python `subprocess` 调绝对路径
- `mix` 脚本顶层子命令有 `setup`、`swag`、`apifox`、`goctl-api`、`goctl-orm`、`lint`、`format`、`dev`、`dist`、`docker`、`docker-services`、`loki`、`compose`、`help`；开发模式必须写全 `./mix dev multi|seq|stop`（**没有** `./mix seq` / `./mix multi` / `./mix stop`，README 历史版本里这三处写错）
- `scripts/run.sh` 的运行工具默认值：`--java-build` 默认 `maven`、`--node-runtime` 默认 `bun`、`--python-runtime` 默认 `uv`
- 两套容器编排的容器名不同：`./mix docker` 用 `mix-<service>-container`，`./mix compose` 用 `mix-<service>`（compose 的 `container_name`）
- `README.md` 行尾由 `.gitattributes` 统一为 LF，批量改文档按「归一化 LF → 断言唯一性后替换」处理，不要逐处手工编辑

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

生成后核对三件事：

1. 新接口出现在产物里，路径、方法、参数与响应结构和实现一致
2. `openapi.json` 与 `openapi.yaml` 成对更新，不要只提交其中一份
3. GoZero 若改了 `.api`，确认产物里没有 `x-date` / `x-goctl-version`（出现即说明 `fix.py` 后处理没跑到）

### 第二步：同步到 Apifox（配置了令牌时执行）

```bash
# 先校验产物与配置，不发起导入请求
./mix apifox --dry-run

# 同步本次改动的服务
./mix apifox spring

# 或同步全部
./mix apifox
```

- 脚本读取的是仓库内的静态产物，**必须先完成第一步**，否则同步上去的是旧文档
- 需要根目录 `.env` 中的 `APIFOX_ACCESS_TOKEN` 与 `APIFOX_PROJECT_ID`；未配置时脚本会直接报错退出，这种情况先提交文档产物，把同步留到配好令牌的环境执行
- 按服务串行导入，输出「新增 / 更新 / 忽略 / 失败」计数；出现失败计数或非零退出码必须排查后重试，不要当成噪声放过
- 覆盖策略默认 `AUTO_MERGE`，保留 Apifox 侧手工维护的中文名、mock 与返回示例，只按文档更新结构化内容
- 令牌等同账号密码，脚本输出不回显令牌，根目录 `.env` 已被 `.gitignore` 忽略

### 接口描述写在代码声明处

产物内容由代码里的注解 / 装饰器决定，新增接口时同步补上，否则文档里只有路径没有说明（注解字符串一律写字面量，按通用规则 5 不抽常量）：

- 响应结构也必须在代码声明中保持可发现：NestJS 控制器为统一响应补充 `ApiResponseModel` 或重定向响应装饰器，FastAPI 路由为统一响应补充 `ApiResponse[T]` 泛型参数。修改后重新生成对应服务的 `docs/openapi.json` 与 `docs/openapi.yaml`，检查响应的 `data` schema 与实际返回值一致。
- Spring：`@Operation(summary, description)`、`@Tag`
- NestJS：`@ApiOperation({ summary, description })`、`@ApiTags`
- FastAPI：`@router.get/post(..., summary=, description=)`
- GoZero：`.api` 中的 `@doc(summary, description)`；handler 的 `ApplyApiLog` 描述不能留 `TODO: 添加接口描述` 占位

## 验证命令

| 服务    | 验证                                                                                                                                |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| spring  | `mvn compile -f spring/pom.xml`（打包 `mvn clean package -DskipTests`）                                                             |
| nestjs  | `npm run node:build`（nestjs 目录）                                                                                                 |
| fastapi | `.venv/Scripts/python.exe -c "import app"` 级导入校验 + pytest                                                                      |
| gozero  | `cd gozero/app && GOTOOLCHAIN=local go build ./... && go vet ./... && go test ./... -count=1`；格式与静态检查走 `./mix lint gozero` |
| gateway | `apisix.yaml` 改动后校验 YAML 语法与目标路由的插件挂载（配置驱动，无业务代码）                                                      |

### 代码风格检查与格式化

生成或修改代码后，先格式化再检查，两者都通过才算完成。省略服务名时处理 spring、gozero、nestjs、fastapi 全部：

```bash
# Spring：Eclipse formatter + import 四段分组，配置在 spring/eclipse-formatter.xml
./mix format spring      # mvn spotless:apply
./mix lint spring        # mvn spotless:check

# GoZero：配置在 gozero/app/.golangci.yml
./mix format gozero      # golangci-lint fmt
./mix lint gozero        # golangci-lint run

# NestJS：配置在 nestjs/.prettierrc 与 nestjs/eslint.config.mjs
./mix format nestjs      # npm run format + npm run lint:fix
./mix lint nestjs        # npm run lint + npm run format:check

# FastAPI：配置在 fastapi/pyproject.toml
./mix format fastapi     # ruff format . + ruff check --fix .
./mix lint fastapi       # ruff check .
```

底层脚本是 `scripts/format.sh` 与 `scripts/lint.sh`，对应工具未安装时该服务会自动跳过并提示；`gateway` 为 APISIX 配置，不参与。行尾由根目录 `.gitattributes` 统一为 LF。
