---
name: mix-fastapi
description: mix-web-demo 的 FastAPI + SQLAlchemy async 服务专项编码规范，覆盖依赖注入三层、全异步、Agent 工具权限与上下文预算。修改 fastapi/ 下代码时加载
---

# mix-fastapi FastAPI 服务规范

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
  - **文件内顺序固定为「装配函数 → 依赖别名」**：`app/dependencies/` 下每个文件先集中写 `provide_*` / `resolve_*` 函数，再把全部依赖别名（`XxxDep = Annotated[...]`，含 `DbSession`、`ClickHouseSession` 这类会话别名）集中在文件末尾构成连续区块，中间不再夹装配函数。由此装配函数的参数不能引用本文件定义的别名（`def` 时注解即求值，别名排在后面会变成前向引用），需要注入另一个服务的实例时写内联 `Annotated[XxxService, Depends(provide_xxx_service)]`。该约定由 `./mix lint fastapi` 里的 `scripts/quality/dependency-aliases.py` 检查，`./mix format fastapi` 会把散落的别名搬到文件末尾；引用本文件别名的装配函数不做自动改写，脚本报出位置后人工改成内联
- 注册范围只含**路由函数签名里直接出现**的依赖（DB 会话 + 服务 + agent 工具）；Client / Mapper / Cache 工厂不注册，只被 `provide_*` 与 `get_*_service` 消费
- `@lru_cache` 工厂是承重墙：`provide_*` 每次请求都会执行，底层工厂漏 `@lru_cache` 会让 `get_xxx_service` 的缓存按新键无界累积
- 非请求链路（APScheduler 任务）用 `resolve_xxx_service()` 复用同一组单例工厂，禁止 `cls(...)` 直接 new（会造出第二个实例、内部状态不共享）
- 全异步：接口必须 `async def`；优先用 asyncio 生态；同步阻塞库（clickhouse_driver、连接池同步接口）用 `asyncio.to_thread(...)` 包裹后 `await`
- 并行：独立 IO 用 `asyncio.gather`；循环内并行把每次迭代封装为内部 async 函数后 gather
- `__init__.py` 导出：包内有 `__init__.py` 导出的功能，导入一律走包路径（`from app.internal.crud import UserAnalysisMapper`），禁止深入到文件路径；新增模块必须同步更新 `__init__.py` 导出。该约定由 `./mix lint` 里的 `scripts/quality/package-imports.py` 检查（目标目录没有 `__init__.py`、与目标同包、或导入方位于目标包导入链上时不受约束），历史违规可执行 `python scripts/quality/package-imports.py --fix fastapi` 批量整理
- `internal/services` 每个业务子目录及 `llm/extend` 都在自身 `__init__.py` 导出公开类和工厂；顶层 `services/__init__.py` 只从子包聚合导出，避免跨层直接指向具体服务文件。新增业务服务时同步维护子包与顶层两级导出
- 类型标注全覆盖；**`import` / `from ... import` 一律写在文件顶部，禁止出现在函数体、类体或条件分支里**（`if TYPE_CHECKING:` 块不受约束，它不参与运行时导入）；确认无法上移的只有两类，必须在导入语句行尾或上一行写 `# lazy-import: 原因`：循环依赖（`app.core.db` 的建表/装图函数导入 `app.internal.models`，models 反向依赖 `core.db`）与明确的延迟加载（`app/__init__.py` 的 `create_app` 门面，避免导入工具模块时初始化数据库驱动与遥测 SDK）。该约定由 `./mix lint fastapi` 里的 `scripts/quality/local-imports.py` 检查，`./mix format fastapi` 会把可整理的导入搬到顶部对应分组（标准库 / 第三方 / `app` 与相对导入各自成组、组内按模块名字典序）；多名字导入、多行括号导入、带行尾注释（如 `# noqa`）与分支内的导入只报位置，需人工处理；生成后检查并删除未使用的 import
- **入参校验用 Pydantic 模型**（放 `internal/schemas/`，文件名 `xxxDTO.py`）：字段用 `Field(...)` 声明，单字段规则用 `@field_validator` + `PydanticCustomError`（中文消息，参考 `createHistoryDTO.py`），请求体禁止用裸 `dict` / `Any` 接收；新增接口必须带校验（通用规则 13）
- **`Field(description=...)` 直接写中文字面量**，实际参与调用的还有 Agent 工具参数模型与结构化输出模型（如 `internal/agents/tools/*.py` 的 `args_schema`、`routing/intentRouter.py` 的 `StructuredIntent`）：不抽 `Messages.*` / `IntentConstants.*` 常量；含变量时用 f-string 或字符串拼接把字面量与变量组合
- **Agent 工具入参 schema 集中放 `internal/agents/tools/toolSchemas.py`**，不进 `internal/schemas/`（那层只放 HTTP 契约 DTO）：多个工具共用的参数模型（`EmptyInput`、`TableSchemaInput`、`SqlQueryInput` 等）写成模块级类直接复用，描述文案依赖运行时清单的（图谱预定义查询名、数仓数据集）写成 `type[BaseModel]` 工厂函数；不要再在 `get_langchain_tools()` 内部定义局部 Pydantic 类，四个 SQL 工具与 MongoDB、数仓、Neo4j 均已收口到该模块
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
- 接口日志：`@log("操作描述")` / `@logWithConfig("操作描述", exclude_fields=[...])` 的描述直接写字面量；**测试接口（`/test` 前缀）与带 `@requireInternalToken` 的内部接口加 `skip_mq=True`**，装饰器仍打印请求日志与耗时（流式与非流式两个上报点都已短路），只是不向 `api-log-queue` 投递
- 上下文：`core/middleware/contextMiddleware.py` 的 contextvars（`get_current_user_id` 等），深层函数免参读取用户信息
- **OpenAPI 文档定制放 `core/swagger/` 包**（实现 `openapi.py`，由 `__init__.py` 导出 `setup_openapi`，调用方只 `from app.core.swagger import setup_openapi`），在 `create_app()` 里紧随 `instrument_fastapi(app)` 调用；由它覆写 `app.openapi`，使用 `SwaggerConfig.OPENAPI_VERSION` 生成并缓存到 `app.openapi_schema`。禁止在 `app.py` 内联 `custom_openapi`（与 NestJS `app/swagger.ts`、GoZero `boot/swagger.go`、Spring `config/SwaggerConfig` 对齐）
- **HTTP 中间件一律放 `core/middleware/`（`XxxMiddleware` 继承 `BaseHTTPMiddleware`），在 `core/middleware/__init__.py` 的 `middlewares` 列表统一注册，禁止在 `app.py` 用 `@app.middleware("http")` 内联**：`add_middleware` 会把后注册的放到最外层，列表因此按「内层 → 外层」声明（当前为 `[MetricsMiddleware, ContextMiddleware]`，跑出来 `Context → Metrics`）；现有两个中间件分别是 `contextMiddleware.py`（上下文/contextvars）与 `metricsMiddleware.py`（Prometheus `mix_http_*` 指标，路由取自 `request.scope["route"]`，必须在 `call_next` 之后读取）
- **类与函数必须带单行中文 docstring**（风格参考 `internal/models/warehouse/base.py`）：类说明职责，方法/函数说明做什么，`__init__` 说明注入了哪些依赖；常量类 `@staticmethod` 用一句话概括消息/常量用途，SQL 模板常量概括查询目的；单行书写、结尾不加中文句号（对齐通用规则 13）；私有方法（`_` 前缀）与嵌套类同样要求，已存在的 docstring 不改写。新增类和函数遗漏 docstring 视同未完成；交付前可用 AST 复核（遍历 `ClassDef` / `FunctionDef` / `AsyncFunctionDef`，`ast.get_docstring` 为 None 的清单必须为空）。**docstring 必须是函数体的第一条语句，实现/步骤注释写在 docstring 之后的空行下面**——禁止把 `# 1. xxx` 之类的注释放在 docstring 上方（注释不参与 `body[0]` 判断，但会让 docstring 位置错乱、IDE 提示与阅读顺序都变形）；复核脚本可扩展为「`body[0]` 是 docstring 且其前面没有纯注释行」
