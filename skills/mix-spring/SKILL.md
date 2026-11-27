---
name: mix-spring
description: mix-web-demo 的 Spring Boot 3 WebFlux + R2DBC 服务专项编码规范，覆盖目录组织、响应式分层与硬性约定。修改 spring/ 下代码时加载
---

# mix-spring Spring 服务规范

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

- **控制器返回类型禁止匿名 Map**：一律用 `entity/vo/` 下的 VO 并给字段加 `@Schema`，`./mix lint spring` 会检查（`scripts/quality/controller-vo.py`）。把原先的 `Map<String, Object>` 换成 VO 时，类上必须加 `@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)` 保持 `user_id`、`create_time` 这类下划线字段名，否则 FastAPI/GoZero 按原字段名解析会取不到值；只有运行时结构不固定（动态列、动态键）时才允许 Map，并在方法或其注解上方写 `// vo-exempt: 原因`，整类场景写 `// vo-exempt-class: 原因`
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
- 接口日志：`@ApiLog("操作描述")` 的描述与 `excludeFields` 字段名直接写字面量；**测试接口（`/test` 前缀）与带 `@RequireInternalToken` 的内部接口加 `skipMq = true`**（`@ApiLog(value = "操作描述", skipMq = true)`），切面仍打印起始日志与耗时，只是不投递 `api-log-queue`
- **响应式切面的固定写法**：`pjp.proceed()` 返回的是**未订阅的冷流**（业务代码此时尚未执行），且 Reactor Context 只在订阅时可见。所以切面必须把校验 / 日志 / 同步挂到 Mono 链上（`Mono.deferContextual(ctx -> ...)`）：校验类用 `validate(ctx).then(businessMono)` 保证「校验先于业务」，副作用类用 `monoResult.doOnSuccess(...)` 发后即忘；副作用里若需要用户身份，必须用 `UserContext.writeContext(Context.empty(), ...)` 重建 Context 再 `contextWrite`，否则异步链上读不到。**禁止用同步代码在 `proceed()` 之前读上下文**，那时 ctx 不可见，只会拿到 null
- **方法可见性顺序**：类（含嵌套类）的实例方法按可见性分组排列，public / protected 方法在前，private 方法在后，private 方法不得穿插在 public / protected 方法之间。static 方法不参与排序（常量类与工具类的 static 方法常与 static 字段成对书写）；字段、构造器、静态初始化块与嵌套类型声明不受约束；只识别带 public / protected / private 修饰符的方法，无修饰符的包私有方法不参与。该约定由 `./mix lint spring` 里的 `scripts/quality/java-method-order.py` 检查，`./mix format spring` 会把 private 方法自动移到 public / protected 之后
- 注入风格：`@Service` + `@RequiredArgsConstructor` + `private final` 字段（构造器注入），禁止字段 `@Autowired`
- 外部基础设施统一由 Spring Bean 提供：`PasswordEncryptor` 注入 `BCryptPasswordEncoder`，禁止在工具或 Service 内部直接 `new` 加密器、客户端或连接资源；新增同类依赖放入 `config` 的 `@Configuration` Bean
- Swagger 用 springdoc：`@Operation(summary, description)`、`@Tag`，注解参数直接写字面量，不抽常量
- 日志：`common/utils/SimpleLogger` 实例注入使用
- **配置项一律声明为 `config/properties/` 下的 `@ConfigurationProperties` record，读取配置只能通过注入这些类，禁止 `@Value` 字段**（main 侧当前已无 `@Value`：`logging.include-timestamp` / `logging.file.path` 由 `LoggingProperties` / `LoggingFileProperties` 承接，`server.mode` / `server.port` 由 `ServerProperties` 承接，`SimpleLogger`、`InitMessageInitializer`、`SwaggerConfig` 均走构造器注入）；配置元数据由 `spring-boot-configuration-processor` 自动生成：类 Javadoc 用 `@param` 写描述（续行不能以 `@` 开头，否则描述会被截断），原始类型组件的默认值必须用 `@DefaultValue` 显式声明（不写会落成 `0` / `false`，与 YAML 的 `${ENV:default}` 漂移），`@ConfigurationPropertiesScan` 负责注册；`META-INF/additional-spring-configuration-metadata.json` 当前不存在，只有确实无法建模的键才新建，补了绑定类后必须同步删掉手写条目；`server` 这类 Boot 自带前缀也能建绑定类，与 Boot 自身的 `ServerProperties` 同前缀共存时双方各绑各的字段、未知键忽略，但自定义配置优先用独立前缀；离线文档切片测试 `OpenApiDocGenerator` 不加载 `@ConfigurationPropertiesScan`，给被 `@Import` 的配置类新增配置依赖时要在 `MockConfiguration` 里补对应 Bean；新增或修改配置键后跑 `./mix compile spring` 并核对 `target/classes/META-INF/spring-configuration-metadata.json` 的 `description` 与 `defaultValue`
- **类（含接口、抽象类、枚举、记录、注解类型）与方法（含构造器）必须带 Javadoc 注释**（风格参考 `infra/client/ServiceRequestOptions.java` 的三行 `/** 微服务请求的可选参数 */`）：类/接口/注解类型说明职责，方法说明做什么及关键语义（响应式语义与下游用途可提及）；单句简体中文、结尾不加中文句号；带注解的声明注释写在首个注解上方；`src/test` 不要求，已存在的注释不改写。新增声明遗漏注释视同未完成
