---
name: mix-workflow
description: mix-web-demo 跨服务协作与交付流程专项规范，覆盖内部接口清理、接口文档收尾、验证命令、测试、格式化、交付顺序与 Git 钩子。涉及接口变更、测试或交付校验时加载
---

# mix-workflow 跨服务协作与交付流程

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
7. **重新生成产物并同步文档**：`./scripts/docs/swag-init.sh <service>`（可选 service 名），需要时 `./mix apifox`。**Spring 删过控制器源文件后必须先清掉 `target/classes` 下的残留 `.class`**——Maven 增量编译不删除已移除源文件的产物，文档生成器扫描 classpath，否则已删接口会继续出现在产物里

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
./scripts/docs/swag-init.sh spring
```

产物落在各服务自己的 `docs/` 目录，每个服务输出 `openapi.json` 与 `openapi.yaml` 两份等价文档：

| 服务    | 产物                           | 生成方式                                                | 前置工具  |
| ------- | ------------------------------ | ------------------------------------------------------- | --------- |
| Spring  | `spring/docs/openapi.json`     | `OpenApiDocGenerator` 隔离 Web 层上下文 + 依赖自动 Mock | Maven     |
| GoZero  | `gozero/app/docs/openapi.json` | `goctl api swagger` → `swagger2openapi` → `fix.py`      | goctl、PyYAML（`fix.py` 派生 YAML 必需）；CI 里 `setup-uv` 会把根目录 `.venv/bin` 注入 PATH 且该环境无 PyYAML，`genSwagger.sh` 的自动探测会误选它，故支持 `SWAGGER_PYTHON` 环境变量显式指定解释器，CI 校验步骤会解析装了 PyYAML 的解释器传入 |
| NestJS  | `nestjs/docs/openapi.json`     | `NestFactory.create(..., { preview: true })`            | Bun       |
| FastAPI | `fastapi/docs/openapi.json`    | 导入`create_app()` 后取 `app.openapi()`                 | uv/Python |

四个服务都是**离线生成**：不启动 HTTP 服务，不连 Nacos / MySQL / Redis / RabbitMQ，也不需要各服务的 `.env`（Spring 的 Nacos 配置拉取由 `spring/src/test/resources/bootstrap.yaml` 覆盖关闭）。对应工具未安装时该服务跳过并提示，其余服务继续生成；`gateway` 为配置驱动，无 OpenAPI 产物。

不便于直接重新生成时可用只读检测脚本判断是否已同步，它备份现有产物、重新生成、逐文件比对后恢复，执行完不修改仓库：

```bash
./mix swag-check              # 检测四个服务
./mix swag-check spring gozero  # 只检测指定服务
```

检测两项：一是重新生成的产物与仓库产物逐文件比对；二是用新生成文档算 `components.schemas` 的 digest（算法与 `apifox-sync.sh` 的 `schemas_digest` 一致），与 `.apifox/<service>.schemas.sha256` 比对。返回码 `0` 一致、`1` 产物或基线未同步（需依次重跑 `./mix swag`、`./mix apifox` 并提交 `.apifox/`）、`2` 工具缺失无法检测。CI 的 `docs-consistency` job 调用它拦截未同步的提交，工具缺失在 CI 同样按失败处理；`apifox-sync.yml` 的 prod 同步只是兜底，交付前必须在本地完成生成与 Apifox 同步。

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
- 按服务串行导入，输出「新增 / 更新 / 忽略 / 失败」计数；出现失败计数或非零退出码必须排查后重试，不要当成噪声放过。导入接口按 **2xx** 判成功：内容无变化时 Apifox 返回 200 并带计数字段，真正落库时返回 **201 且响应体为空**，此时脚本不打印计数而是提示「以模型引用自检为准」，不要把空响应当成同步失败，也不要把它显示成「新增 0 / 更新 0」
- 覆盖策略默认 `AUTO_MERGE`，保留 Apifox 侧手工维护的中文名、mock 与返回示例，只按文档更新结构化内容
- **同步默认以文档为准做全量对齐**：`APIFOX_DELETE_UNMATCHED_RESOURCES` 默认 `true`，对应开放 API 的 `options.deleteUnmatchedResources`，会删除**该服务导入目录内**（`APIFOX_FOLDER_*`）文档里没有的接口与数据模型（本地实测：只同步 fastapi 时项目接口总数 217 → 210，正好清掉 fastapi 目录内的 7 个残留，其它服务目录未受影响；Apifox 的 WebSocket 接口是独立资源类型，删除后仍完好）。所以删掉代码里的接口后，重新生成产物再同步即可自动清理，**不需要手工删 Apifox 接口**
- 对齐是全量覆盖语义：Apifox 侧手工新增的 HTTP 接口与数据模型会在下次同步时被清掉（`WebSocket` 与 Markdown 文档不受影响）。排查期可临时关闭：`APIFOX_DELETE_UNMATCHED_RESOURCES=false ./mix apifox <service>`；删除是真实删除，可先 `apifox export --project <id> --format apifox --scope all --output <file>` 整项目备份，误删内容可从 Apifox 回收站找回
- **警惕「AUTO_MERGE + 全量对齐」组合造成接口响应结构引用断链**：`AUTO_MERGE` 不整体重写已存在接口的响应结构绑定，而 `APIFOX_DELETE_UNMATCHED_RESOURCES=true` 会删除文档里已不存在的数据模型。当模型命名变化（例：Spring 补 Swagger 注解后 springdoc 改变 `Result«XxxVO»` 的生成名）时，接口上残留的 `$ref` 仍指向被清理的旧模型，Apifox「校验响应」报 `can't resolve reference #/definitions/<数字ID> from id http://json-schema.org/draft-04/schema#`（数字 ID 是 Apifox 数据模型的内部 ID，产物本身引用链完好）。**已由脚本自动切换**：`apifox-sync.sh` 为每个服务计算 `components.schemas` 的规范化 sha256（只关心模型本身，与排版、字段顺序、paths 调整无关），与 `.apifox/<service>.schemas.sha256` 里上次成功同步的指纹比对——指纹变化或首次无记录时，该服务本轮自动切到 `OVERWRITE_EXISTING` 并打印原因；指纹未变则保持默认 `AUTO_MERGE`。显式设置了 `APIFOX_ENDPOINT_OVERWRITE_BEHAVIOR` / `APIFOX_SCHEMA_OVERWRITE_BEHAVIOR` 时以显式值为准、不做自动切换；只有导入成功才写回指纹，失败保留旧值以便下次重试。**`.apifox/` 必须随仓库提交**：它记录的是「共享 Apifox 项目当前已同步到哪个模型版本」这一远端基线，不是本机状态。漏提交会让其他机器的指纹停留在旧值、误判为「模型有变」而触发覆盖同步，把已保留的手工 Mock 与示例冲掉；同理，同步成功后要与 `docs/` 产物一起提交它。**手工修复**（自动机制被显式配置绕过时）——`APIFOX_ENDPOINT_OVERWRITE_BEHAVIOR=OVERWRITE_EXISTING APIFOX_SCHEMA_OVERWRITE_BEHAVIOR=OVERWRITE_EXISTING ./mix apifox <service>`，跑完恢复默认 AUTO_MERGE；代价是该服务接口上手工维护的参数说明、Mock 与示例会被产物覆盖。应急也可在 Apifox 接口「返回响应 → 数据结构」里手工重新绑定现行数据模型。预防：凡是重命名/调整 VO 或响应包装导致 springdoc/文档生成器模型名变化，同步前先跑一次 OVERWRITE_EXISTING 再回到 AUTO_MERGE
- 导入前会为**本轮文档新增**的接口补写 Apifox 责任人扩展 `x-apifox-maintainer`（值取团队内昵称或用户账户名），默认取 `APIFOX_ACCESS_TOKEN` 对应账号的用户名；可用 `APIFOX_MAINTAINER` 显式指定，或用 `--no-maintainer` 关闭填充
- **数据模型目录必须按服务隔离（`can't resolve reference` 的根本修复）**：`deleteUnmatchedResources` 的清理范围是「该服务的导入目录」。接口早有 `APIFOX_FOLDER_<服务>` 按服务分开，但数据模型此前都落在项目根目录，于是任一服务的全量对齐都会删掉其它服务刚同步的模型，而接口上的 `$ref` 不会回滚 —— 产物本身引用链完好，Apifox「校验响应」却报 `can't resolve reference #/definitions/<数字ID>`。现在脚本按服务下发 `targetSchemaFolderId`（`APIFOX_SCHEMA_FOLDER_SPRING/GOZERO/NESTJS/FASTAPI`，未配置时回退 `APIFOX_SCHEMA_FOLDER_ID`），全量对齐只清理本服务目录内的模型；开启全量对齐却有服务没配模型目录时，脚本直接告警并给出 `apifox folder create --project <项目ID> --type schema --name <服务名>` 的修复命令
- **数据模型目录缺失时的断链排查与修复**：Apifox「校验响应」大面积报 `can't resolve reference #/definitions/<数字ID>` 时，先看 `./mix apifox-check` 输出的模型总数——若远少于各服务 `docs/openapi.json` 里 `components.schemas` 数量之和，说明模型没有落库，而不是产物引用写错。判定方式是 `apifox folder list --project <项目ID> --type schema` 取现存模型目录，与 `.env` 的 `APIFOX_SCHEMA_FOLDER_SPRING/GOZERO/NESTJS/FASTAPI` 逐一比对：目录缺失的服务，其模型在 `apifox schema list` 里同样查不到。原因是导入下发的 `targetSchemaFolderId` 指向已不存在的目录，模型无处落库（`apifox schema create` 同样返回 `404000 Not found`），而接口上原有的 `$ref` 不会回滚，最终整批断链。**此状态下 `./mix apifox <service>` 仍可能打印「新增 0 / 更新 0」**，不能据此判断同步成功，必须以 `./mix apifox-check` 的断链数为准。修复顺序：① `apifox folder create --project <项目ID> --type schema --name <服务名>` 重建目录并记下新 ID；② 把新 ID 写回 `.env` 的 `APIFOX_SCHEMA_FOLDER_<服务>`（本地文件、不入库，需同步给协作者）；③ `APIFOX_ENDPOINT_OVERWRITE_BEHAVIOR=OVERWRITE_EXISTING APIFOX_SCHEMA_OVERWRITE_BEHAVIOR=OVERWRITE_EXISTING ./mix apifox <服务> --no-readme`，覆盖模式下接口会重新绑定到重建后的模型；④ `./mix apifox-check` 复核到「引用完整」。`apifox-sync.sh` 已内置预检 `assert_schema_folders_exist`：配置的目录不存在时在导入前直接报错并给出上述修复命令
- **禁止手工删除 Apifox 的「数据模型」目录，也不要把多个服务配到同一个模型目录**：删目录不会回收接口上的 `$ref`，共用目录会被各服务的 `deleteUnmatchedResources` 互相清空，两者最终都表现为整批 `can't resolve reference`。调整模型目录后必须同步更新 `.env` 的 `APIFOX_SCHEMA_FOLDER_<服务>`，并按上一条的修复顺序重导一次
- **同步后自检并自动修复断链**：导入结束后导出一次项目快照（`apifox export --format apifox`），由 `scripts/docs/apifox-schema-refs.py` 比对接口里 `#/definitions/<模型ID>` 与 `apifox schema list` 的现存模型，统计断链；命中时对本轮服务按 `OVERWRITE_EXISTING` 重导一次重新绑定，再复核一遍，仍有残留才报错退出（`APIFOX_VERIFY_SCHEMA_REFS=false` 可关闭自检）
- **只读检查入口 `./mix apifox-check`**：不改代码、只确认远端引用状态时用它（`--keep <目录>` 保留快照、`--examples <n>` 调整示例条数、`--no-color` 关彩色），输出「接口 N 个，数据模型 M 个」并逐条列出断链位置，退出码 0 完整 / 1 断链 / 2 缺配置或依赖。它需要联网与 `.env` 令牌，因此**不并入离线的 `./mix lint`**
- **责任人只补新增接口**：脚本先用一次 `apifox endpoint list` 取现有接口清单（`method path`），与产物求差集后只给新增接口注入扩展。原因是 Apifox 对「无差异导入」按不变处理（本地实测 `新增 0 / 更新 0 / 忽略 0 / 失败 0`），而每轮给全部接口重写扩展会让所有接口都被判定为已修改（修改时间与变更历史被刷新）；稳态下导入的就是原文档，计数全 0。要整体重写责任人时置 `APIFOX_MAINTAINER_FORCE=true`（此时退回逐接口全量注入）
- 该扩展会被 Apifox 保留在接口 `oasExtensions` 里并在文档页多渲染一行 `x-apifox-maintainer`，**只有真的注入过**才会再导入一次不带扩展的原文档把它清掉（`APIFOX_MAINTAINER_CLEAN_EXTENSION=false` 可保留，此时按全量注入以保证每轮导入内容与 Apifox 现存一致），责任人字段不受影响
- 令牌等同账号密码，脚本输出不回显令牌，根目录 `.env` 已被 `.gitignore` 忽略
- `./mix apifox` 现在一次做完两件事：接口走开放 API 导入，README 走 Apifox CLI（`doc create` / `doc update`）写入 `APIFOX_README_DOC_ID` 指定的项目 Markdown 文档；README 目标未配置或未装 CLI 时该步骤跳过并提示，不影响接口导入。`--no-readme` 只同步接口，`--create-readme` 首次创建 README 文档，单独同步用 `./mix apifox-readme`
- **WebSocket 接口走独立通道**：Apifox CLI 有 `websocket list/get/create/update/delete` 命令族（顶层 `--help` 不列出，由 `cli-schema list` 的 `websocket-create` / `websocket-update` 暴露），与 HTTP 接口的 `import-openapi` 互不影响。`apifox-sync.sh` 对 gozero 额外执行一步：读 `gozero/app/docs/websocket.json` → `websocket list` 按 `path` 匹配接口 ID → `websocket get` 取完整资源 → **先比对现有 `description`/`tags` 与产物是否一致，一致则跳过 update（不刷新修改时间与变更历史）** → 不一致才只覆盖这两个字段 → `cli-schema validate websocket-update` 校验 → `websocket update`；日志中的「未变跳过」即比对后无需更新的数量，不代表同步失败
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

**Windows 主机上，fastapi 的 `./mix compile fastapi` 与 `./mix test fastapi` 不要用 WSL 的 bash 执行（仅 Windows + WSL 场景，Linux/macOS 按默认命令即可）**：底层是 `uv run`，WSL 里的 Linux uv 会清空并重建 Windows 创建的 `fastapi/.venv`（机制与处置见 `mix-engineering` 的依赖环境条目）。这两步在 Windows 上只在 Git Bash 里跑，或改用 `fastapi/.venv/Scripts/python.exe` 的只读等价命令。

### 单元测试与测试工具

各服务的测试工具与运行入口固定，不要引入第二套测试框架；测试分层、必测矩阵与编写规则见 `references/unit-testing.md`：

| 服务    | 测试工具                                                                                              | 命令                                                             |
| ------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| spring  | JUnit 5（Jupiter）+ Mockito + AssertJ；响应式链用 `StepVerifier`，Controller 用 `WebTestClient`       | `./mix test spring`（`cd spring && mvn test`）                   |
| nestjs  | Jest + ts-jest（配置在 `nestjs/package.json` 的 `jest` 段）                                           | `./mix test nestjs`（`bun run test -- --runInBand`）             |
| fastapi | pytest，异步用例用 anyio 插件的 `@pytest.mark.anyio`                                                  | `./mix test fastapi`（`cd fastapi && uv run pytest -q`）         |
| gozero  | Go 标准库 `testing` + `net/http/httptest`，断言可用 testify `assert`（未引入 mock / suite / sqlmock） | `./mix test gozero`（`cd gozero/app && go test ./... -count=1`） |
| gateway | 无单元测试（配置驱动，不参与）                                                                        | `./mix test gateway` 直接跳过                                    |

工具未安装时该服务返回码 2 并跳过，「跳过」不能当成「通过」；只要改动了服务代码或测试，`./mix test <service>` 就是交付前必跑项（顺序见下一节）。

**NestJS 的 spec 必须同时能被 Jest 与 `bun test` 执行**：`./mix test nestjs` 与 `bun run test` 走的是 Jest（仓库基线，用 `ts-jest` 转换），而 `bun test` 走的是 Bun 内置 `bun:test` 与一层 `jest` 兼容层，两者 API 并不完全对齐。因此 spec 只使用两者都提供的 API（`jest.mock`、`jest.fn`、`jest.spyOn`、`jest.restoreAllMocks` 与 `expect.*`），**禁止 `jest.requireActual`、`jest.requireMock`、`jest.unmock`、`jest.deepUnmock`**，也禁止 `import ... from "bun:test"` 或为兼容新增双导出层，仓库不维护两套测试入口。mock 系统边界（如 `node:http`）时在工厂里显式返回被测代码真正用到的成员即可。报错 `TypeError: jest.requireActual is not a function` 表示用 `bun test` 跑到了含 Jest 专有 API 的 spec，修改 spec 而不是换运行器。

### 代码风格检查与格式化

生成或修改代码后，先格式化再检查，两者都通过才算完成。省略服务名时处理 spring、gozero、nestjs、fastapi 全部：

```bash
# Spring：Eclipse formatter + import 四段分组，配置在 spring/eclipse-formatter.xml
# lint 额外执行 scripts/quality/controller-vo.py（控制器是否返回匿名 Map）、scripts/quality/constants.py（常量注释与分类）
# 与 scripts/quality/java-method-order.py（方法可见性顺序）
./mix format spring      # 方法可见性顺序整理（private 移到 public/protected 之后）+ mvn spotless:apply
./mix lint spring        # mvn spotless:check + 控制器返回类型检查 + 常量规范检查 + 方法可见性顺序检查

# GoZero：Go 配置在 gozero/app/.golangci.yml，.api 文件用 goctl api format
./mix format gozero      # golangci-lint fmt + goctl api format
./mix lint gozero        # 常量规范检查 + golangci-lint run + .api 格式检查（临时目录格式化后 diff）

# NestJS：配置在 nestjs/.prettierrc 与 nestjs/eslint.config.mjs
./mix format nestjs      # npm run format + npm run lint:fix
./mix lint nestjs        # npm run lint + npm run format:check + 常量规范检查

# FastAPI：配置在 fastapi/pyproject.toml；lint 额外执行 scripts/quality/constants.py（常量注释与分类）、
# scripts/quality/package-imports.py（包导入规范）、scripts/quality/local-imports.py（import 写在文件顶部）
# 与 scripts/quality/dependency-aliases.py（装配函数在前、依赖别名集中在末尾）
./mix format fastapi     # 模块级导入上移 + ruff format . + ruff check --fix . + 包导入整理 + 依赖别名整理
./mix lint fastapi       # ruff check . + pyright + 常量规范检查 + 包导入规范 + 模块级导入规范 + 依赖别名规范
```

底层脚本是 `scripts/quality/format.sh` 与 `scripts/quality/lint.sh`，对应工具未安装时该服务会自动跳过并提示；`gateway` 为 APISIX 配置，不参与。行尾由根目录 `.gitattributes` 统一为 LF。

### 交付前校验顺序

改完代码后按固定顺序自检，任一步未通过都不算完成（各步命令与底层实现见「验证命令」与「代码风格检查与格式化」章节）：

```bash
./mix format <service>    # 1. 自动格式化
./mix lint <service>      # 2. 代码检查
./mix compile <service>   # 3. 编译校验（只编译，不打包）
./mix test <service>      # 4. 单元测试
```

Windows 主机上执行第 3、4 步时，fastapi 必须在 Git Bash 里跑（WSL bash 中的 `uv run` 会重建 `.venv`，此项只影响 Windows + WSL，Linux/macOS 不受影响）；用不带服务名的 `./mix compile` / `./mix test` 会连带 fastapi，同样要在 Git Bash 执行，或把 fastapi 换成 `fastapi/.venv/Scripts/python.exe` 的只读等价命令

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
- 钩子是 bash 脚本，由 Git 自带的 `sh` 执行：Linux/macOS 直接可用，Windows 走 Git for Windows 自带的 Git Bash；换行符由 `.gitattributes` 统一为 LF
- 新克隆的仓库需执行一次 `./mix hooks` 才会启用；生成代码时不要依赖钩子替代手动校验，钩子有跨服务共享脚本的覆盖缺口（改 `scripts/` 下的检查脚本本身不会触发服务检查）

`mix` 脚本顶层子命令完整列表见 `mix-engineering` 的仓库工程约束章节。
