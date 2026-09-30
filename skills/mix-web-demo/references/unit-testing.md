# mix-web-demo 单元测试规范

## 适用范围

创建、修改、删除或评审测试，以及修复需要回归测试的缺陷时使用本规范

目标是稳定验证权限、核心业务规则、状态迁移、远程调用契约和异常分支，不以测试数量或覆盖率数字代替有效断言

## 测试分层

### 单元测试

单元测试验证一个类、函数或较小业务单元，必须满足：

- 不连接真实数据库、Redis、MQ、Nacos、Elasticsearch、ClickHouse、Neo4j、pgvector、OSS 或外部 HTTP 服务
- 不读取真实 `.env`、`application.yaml`、开发者本地文件或云凭据
- 不监听真实端口，不依赖本机网络状态、操作系统错误文案或测试执行顺序
- 时间、随机数、UUID、HTTP 客户端和持久化依赖可替换
- 默认可并行、可重复执行，单条测试通常在 200ms 内完成
- 允许使用内存对象、Fake、Stub、Mock、`httptest` 和框架轻量测试工具

### 组件测试

组件测试允许启动框架上下文，但所有外部基础设施必须替换为测试实现。适用场景：

- Spring `WebTestClient` 验证 Controller、校验和异常映射
- NestJS `TestingModule` 验证 Guard、Pipe、Filter 和 Controller
- FastAPI `TestClient` / `httpx.AsyncClient` 验证路由与依赖注入
- Go `httptest` 验证 Handler 与 Middleware 链
- WebSocket/SSE 从连接接入、消息处理到本地 Hub 状态的链路

### 集成测试

以下行为依赖真实协议或数据库语义，不要伪装成单元测试：

- R2DBC、sqlx、SQLAlchemy、TypeORM、Mongoose 的真实查询、事务、锁和回滚
- Redis 锁、缓存与 Pub/Sub 跨实例行为
- RabbitMQ 确认、重投和重复消费
- Elasticsearch、ClickHouse、Neo4j、pgvector 查询
- Nacos 服务发现、代理和连接池行为
- OSS 上传、下载和删除
- 浏览器 WebSocket 到数据库已读状态的完整链路

集成测试必须与默认单元测试命令分离，明确环境变量，并优先使用 Testcontainers 或独立测试环境

## 通用编写规则

- 使用 Arrange、Act、Assert 结构；一个测试只描述一个业务行为
- 测试名同时表达条件和结果，例如 `should_not_retry_on_downstream_400`
- 参数边界使用表驱动或参数化测试，禁止 `test1`、`normalCase`、`shouldWork` 等模糊名称
- 至少断言返回关键字段、异常类型/错误码、状态变化或关键依赖参数之一；禁止只断言“不抛异常”或“结果非空”
- 只 Mock 系统边界：Repository、Model、Mapper、Session、缓存、MQ、OSS、服务发现、远程 Client、时钟、随机数和文件系统
- 不 Mock 被测对象自身的私有方法；若业务类因具体依赖无法测试，先提取窄接口
- 不断言普通日志文本、私有方法调用次数或第三方库内部实现，除非日志本身是审计要求
- 默认测试不得输出 Token、密码、密钥、完整连接串或用户隐私数据
- 安全测试使用固定假密钥，例如 `unit-test-secret`，不得加载真实配置
- 修改环境变量、contextvars、全局缓存或单例后必须恢复；临时文件使用临时目录并注册清理

## 异步与并发

- 禁止使用任意时长的 `sleep` 等待异步结果
- 使用事件、Channel、Latch、虚拟时钟、Fake Timer 或可控 Promise 同步
- 所有异步调用必须被 `await`、订阅或消费
- 测试结束后清理定时器、连接、协程、goroutine、线程池和熔断器
- 并发逻辑覆盖部分失败、取消、超时和资源释放
- Go 共享状态包在 Linux CI 定期执行 `go test -race`；本机未启用 CGO 不应阻塞普通单元测试

## 必测矩阵

### 权限与认证

新增或修改权限注解、Decorator、Guard、Middleware 或资源归属规则时，至少覆盖：

| 场景 | 预期 |
| --- | --- |
| 未登录或上下文缺失 | 401 或项目约定的未登录错误 |
| 当前用户访问自身资源 | 放行，且不额外查询管理员权限 |
| 管理员访问其他用户资源 | 放行 |
| 普通用户访问其他用户资源 | 403 |
| 目标用户或资源参数缺失 | 400，禁止默认放行 |
| 目标资源不存在 | 404 或项目约定错误 |
| 批量资源属于不同用户 | 整体拒绝，禁止部分放行 |
| 管理员校验服务异常 | fail-closed |
| 内部 Token 缺失、过期、篡改或服务名不匹配 | 拒绝访问 |

### 跨服务调用

修改统一远程调用封装时，根据实际分支覆盖：

- 首次调用成功
- 网络超时、连接失败、HTTP 5xx 按配置重试
- HTTP 4xx 和业务错误不重试
- 达到最大次数后返回最后一次错误或约定降级结果
- 调用方 Context 取消后停止退避和后续请求
- 熔断打开时执行约定降级
- 透传 `X-User-Id`、`X-Username`、`X-Session-Id`、`Authorization`
- 生成并发送 `X-Internal-Token`；未登录系统调用使用 `userId=-1`
- 非法 JSON、响应体读取失败和服务发现失败

退避使用虚拟时间、零退避配置或可注入 Sleeper，不真实等待。不要重复测试 Resilience4j、axios-retry、tenacity、opossum 等第三方库自身算法，只验证项目配置和可观察行为

### 数据写入与状态迁移

根据业务风险覆盖正常写入、目标不存在、重复请求幂等、并发更新、失败回滚、用户/资源范围、批量空集/重复 ID/部分不存在，以及依赖报错时不得报告成功

复杂 SQL、事务和数据库方言使用集成测试；单元测试验证 Service/Logic 对依赖结果的处理。sqlmock 只验证关键条件与参数，不把完整 SQL 文本格式当业务契约

### 实时消息

本地可单测连接注册、多连接替换和清理、`ping/pong`、目标用户隔离、已读回执绑定当前连接用户、持久化失败不确认、`lastMessageId` 边界以及 WebSocket/SSE 回退

Redis Pub/Sub 跨实例去重、真实断线重连、浏览器持续打开窗口到数据库已读的完整行为属于组件或集成测试

## 各服务约定

### Spring WebFlux

- 测试放在 `spring/src/test/java/<生产包路径>/XxxTest.java`
- Reactor 链使用 `StepVerifier`，禁止 `.block()`
- Reactor Context 用 `contextWrite` 显式构造
- Controller、参数校验和异常映射使用 `WebTestClient`
- Service 依赖使用 Mockito 或小型 Fake；保持 Mockito 严格模式，不用宽松 stub 掩盖无关依赖
- R2DBC SQL 和事务使用 Testcontainers 集成测试
- AOP 测试必须订阅 Mono 并验证订阅后的行为
- 默认命令：`cd spring && mvn test`

### NestJS

- 单元测试放在 `nestjs/src/**/xxx.spec.ts`
- 组件/集成测试放在 `nestjs/test/integration/**/*.integration-spec.ts`，端到端测试放在 `nestjs/test/e2e/**/*.e2e-spec.ts`
- Service、Guard、Filter、Middleware 使用 `TestingModule` 或直接构造；外部 Provider 用 `useValue`、`useFactory` 或 Token 替换
- 每个测试恢复 Mock；定时器、批处理和重试使用 Fake Timers
- 默认测试禁止加载真实应用配置或触发连接外部服务的 `onModuleInit`
- 项目只以 Jest 为测试基线；`bun run test -- --runInBand` 调用的是 Jest，不要使用 `bun test` 或新增 `bun:test` 兼容层
- 默认命令：`cd nestjs && bun run test -- --runInBand`

### FastAPI

- 测试沿用 `fastapi/tests/<应用包路径>/xxx_test.py`；引入 integration marker 后再拆分独立集成目录
- 异步测试使用 pytest/AnyIO，异步依赖使用 `AsyncMock`
- 路由组件测试使用 `dependency_overrides`
- 每个测试清理 dependency override、contextvars、`lru_cache` 单例和共享熔断器状态
- SQLAlchemy Session、HTTP Client、Redis 和 MQ 不得在单元测试中真实连接
- 后台任务直接调用核心 async 函数，不依赖 APScheduler 触发
- 默认命令：`cd fastapi && .venv/Scripts/python.exe -m pytest -q`

### GoZero

- 测试与生产包同目录，命名 `xxx_test.go`
- 边界和错误分类优先表驱动；资源使用 `t.Cleanup` 回收
- HTTP 使用 `httptest.Server` 或注入 `RoundTripper`
- sqlx Model 使用 `sqlmock` 验证条件和参数；关键 SQL 另加 MySQL 集成测试
- Logic 通过窄 Model/Client 接口注入依赖，不为测试在 Logic 中增加 SQL
- Middleware 使用 `httptest.NewRecorder` 验证状态码、响应体、Context 和 Body 恢复
- goctl 生成的 DTO、Handler 脚手架不要求逐文件覆盖，但手写 `Validate()` 和路由中间件绑定必须测试
- 默认命令：`cd gozero/app && go test ./... -count=1`

## OSS 专项边界

NestJS 默认 OSS 单元测试必须使用显式假配置、Mock OSS Client/Adapter 和临时文件或 Buffer，不读取 `.env`、静态图片或真实凭据，不执行真实上传

真实 OSS 测试放到独立 integration 测试集，仅在显式环境开关与专用测试 Bucket 可用时运行，Object Key 使用测试前缀，结束后删除对象

## 覆盖率与取舍

- 新增或修改的业务代码目标：行覆盖率不低于 80%，分支覆盖率不低于 70%
- 权限、认证、重试、幂等和状态迁移目标：行与分支覆盖率不低于 90%
- 使用主分支覆盖率作为增量基线，不要求一次性为全仓历史代码补齐数字
- 生成代码、DTO、PO、Schema 字段、常量、启动入口和迁移可排除
- 不为 getter、响应包装参数排列、薄 Controller 转发或第三方库内部行为增加低价值测试
- Bug 修复必须包含能在修复前失败、修复后通过的回归测试

## 提交前检查

- 默认测试在无 Docker、无云凭据、无真实 `.env` 的环境通过
- 断言覆盖失败分支和状态变化，不只是成功路径
- 权限测试覆盖本人、管理员、其他用户和依赖异常
- 远程调用覆盖重试、取消、4xx 不重试、内部 Token 和降级
- 异步测试没有固定 `sleep`，资源已清理
- 测试日志没有凭据和隐私数据
- 没有为了覆盖率测试生成代码、DTO、getter 或第三方库实现
- 只运行受影响服务的格式、静态检查、构建和全量单元测试；外部基础设施场景进入独立集成测试
