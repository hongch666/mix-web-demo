---
name: mix-nestjs
description: mix-web-demo 的 NestJS + Fastify 服务专项编码规范，覆盖模块组织、双 ORM 分工、CLS、校验与命名转换。修改 nestjs/ 下代码时加载
---

# mix-nestjs NestJS 服务规范

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

### 包导出与 import 约定

- 聚合目录必须通过 `index.ts` 具名导出公开成员：`common/{exceptions,interfaces,utils}`、`framework/{decorators,explorer,filters,guards,interceptors,middleware}`、`module/common/{cache,client,github,logger,mail,nacos,oss,redis,telemetry,word}`、`module/system/{apiLog,articleLog,download,logDeletion,mongoTools,ossObject,sqlTools,tableSettings,task,test,upload}`。新增实现文件时同步更新所属目录的 `index.ts`，禁止无意义地建空入口或用 `export *` 模糊公开边界
- 跨目录引用一律从目录入口导入（`import { LoggerService } from "src/module/common/logger"`），禁止指向具体文件（`import { LoggerService } from "src/module/common/logger/logger.service"`）；同目录实现互引保留 `./xxx` 相对路径，`index.ts` 自身直接引用实现文件属于必要写法
- 例外：`module/common/common.module.ts` 与 `module/system/system.module.ts` 是 Nest 模块聚合点，不再套 `index.ts`；`app/index.ts` 是带遥测副作用的应用工厂，`config/index.ts` 是配置加载入口，两者都不是 barrel；`module/common/telemetry/instrumentation.ts` 必须保持直接副作用导入；导入方位于目标 `index.ts` 的导入链上时允许保留具体文件引用以避开循环依赖，例如 `framework/explorer/cache.explorer.ts` 直接引用 `cache.service`
- 副作用导入（`import "xxx"`）、动态 `import()` 与 `.d.ts` 的三斜线引用不受上述约束
- 该约定由 `./mix lint nestjs` 里的 `scripts/quality/ts-package-imports.py` 检查；`./mix format nestjs` 会把深层导入改为目录入口、合并同一目标的重复具名 import，名字按首次出现顺序保留

### 模块内组织与约定

- 每个业务模块：`xxx.module.ts` + `xxx.controller.ts` + `xxx.service.ts`，辅以 `dto/` 与 `schema/`（Mongoose）或 `entities/`（TypeORM）
- ORM 按模块现状选择：日志类用 Mongoose（`@Schema` + `SchemaFactory`，`@InjectModel`）；结构化表用 TypeORM（`@InjectRepository`）。新模块先参考同类模块，禁止凭空引入新 ORM
- **入参校验走全局 `ValidationPipe`（`app/index.ts` 注册，`transform` + `enableImplicitConversion`），DTO 用 class-validator 注解**；新增接口必须带校验（通用规则 13），每个 `@Body()` / `@Query()` / `@Param()` 都要有对应 DTO 与约束注解，直接用裸参数接请求等于没有校验。自定义 `exceptionFactory` 把错误包成 `BusinessException(400, PARAM_PARSE_FAILED)`，最终由 `AllExceptionsFilter` 输出统一结构。**当前未开 `whitelist` / `forbidNonWhitelisted`**，未声明字段既不剥离也不报错，不要依赖"多余字段会被拒"
- 请求上下文用 nestjs-cls：`ClsMiddleware` 写入（userId/username/sessionId/token/internalToken），业务注入 `ClsService` 读取；gRPC 或脱离 HTTP 异步链的场景必须用 `ClsService.run` 手动开启上下文
  - **未登录语义注意**：`parseUserId` 要求 `Number.isInteger(userId) && userId > 0`，所以 ≤0 的值（含约定的系统调用 `-1`）在 CLS 里是 `undefined`；出站头由 `NacosService.call` 生成（`X-User-Id: String(userId || 0)`，内部令牌按 `userId > 0 ? userId : -1`）。需要区分"未登录 / 系统调用"时不要直接依赖 CLS 的值
- 公共层入口是 `module/common/common.module.ts`：作为**系统级模块的集中加载点**，`imports` 收拢所有需在应用启动时实例化的公共模块（Telemetry、Logger、Redis、Cache、Nacos、Client、Github、Mail），让 Redis 客户端、缓存订阅与全量扫描、Nacos 注册、遥测停机钩子等生命周期逻辑只在一处触发；`exports` 导出 ClientModule 与 NacosModule，前者供根模块 `RequireAdminGuard`/`RequireSelfGuard` 注入 `SpringClientService`，后者供根模块 `InternalTokenGuard` 注入 `InternalTokenUtil`，缺一会导致 DI 解析失败
- 业务模块用到公共能力（oss、word、redis、nacos 等）仍由消费方**自行 import 对应模块**，依赖关系保持显式；CommonModule 的 `imports` 只负责实例化、不替业务模块中转 provider，禁止把它当成"全量中转池"（那会让模块边界形同虚设）；定时任务（TaskModule）属系统业务，放 `module/system/task`，不进 CommonModule，避免 common 层反向依赖 system 层
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
- 接口日志：`@ApiLog("操作描述")` 或 `@ApiLog({ message, excludeFields })`，描述与字段名直接写字面量；**测试接口（`/test` 前缀）与带 `@RequireInternalToken()` 的内部接口写 `@ApiLog({ message: "操作描述", skipMq: true })`**，`ApiLogInterceptor` 仍记录本地请求日志与耗时，只是不向 `api-log-queue` 投递
- **类、接口、函数与方法必须带 JSDoc 注释**（风格参考 `common/utils/batchBuffer.ts` 的三行 `/** 攒批配置选项 */`）：Service/Controller/Module/DTO/接口说明职责，方法说明做什么及关键语义；单句简体中文、结尾不加中文句号；带装饰器的声明注释写在首个装饰器上方；`*.spec.ts` 不要求，已存在的注释不改写。新增声明遗漏注释视同未完成
