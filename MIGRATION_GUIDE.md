# gozero MySQL 直连迁移至 Spring 远程调用 — 改造文档

## 一、改造背景

gozero 服务原本通过 sqlx 直接连接 MySQL 数据库，操作 `articles`、`user`、`category`、`category_reference`、`collects`、`comments`、`focus`、`likes`、`sub_category` 共 9 张业务表。为统一数据访问入口、降低数据库连接复杂度，将这些表的读写操作全部迁移到 Spring Boot 服务，gozero 通过 HTTP 远程调用 Spring 的内部接口获取数据。

**保留的表**：
- `chat_messages` — 聊天消息表，由 gozero 专门维护，不迁移
- `ai_history` — AI 历史记录表，由 FastAPI 维护，gozero 仅保留 model 定义备用

## 二、改动范围概览

| 服务 | 新增文件 | 修改文件 | 删除文件 |
|------|---------|---------|---------|
| Spring | 1 | 14 | 0 |
| gozero | 2 | 7 | 27 |

## 三、Spring 改动详情

### 3.1 新增文件

| 文件 | 说明 |
|------|------|
| `entity/dto/CommentScoreDTO.java` | 评论评分 DTO，包含 `averageScore`（平均分）和 `count`（评论数）两个字段 |

### 3.2 新增内部接口（7 个）

所有接口均标注 `@RequireInternalToken`，通过 JWT 内部令牌进行服务间认证。

| 接口 | 方法 | 路径 | 所属 Controller | 用途 |
|------|------|------|-----------------|------|
| 文章阅读量批量查询 | POST | `/articles/views/batch` | ArticleController | esSyncerTask / SearchModel |
| 评论评分批量查询 | POST | `/comments/scores/batch` | CommentsController | esSyncerTask |
| 点赞数批量查询 | POST | `/likes/counts/batch` | ArticleLikeController | esSyncerTask / SearchModel |
| 收藏数批量查询 | POST | `/collects/counts/batch` | ArticleCollectController | esSyncerTask / SearchModel |
| 粉丝数批量查询 | POST | `/focus/counts/batch` | FocusController | esSyncerTask / SearchModel |
| 分类批量查询 | POST | `/category/batch` | CategoryController | esSyncerTask |
| 子分类批量查询 | POST | `/category/sub/batch` | CategoryController | esSyncerTask |

### 3.3 扩展的 Service 接口

| 接口 | 新增方法 | 说明 |
|------|---------|------|
| `ArticleService` | `getArticleViewsByIDs(Collection<Long>)` | 批量查询文章阅读量，返回 `Map<Long, Integer>` |
| `ArticleLikeService` | `getLikeCountsByArticleIds(Collection<Long>)` | 批量查询点赞数，返回 `Map<Long, Long>` |
| `ArticleCollectService` | `getCollectCountsByArticleIds(Collection<Long>)` | 批量查询收藏数，返回 `Map<Long, Long>` |
| `FocusService` | `getFollowCountsByUserIds(Collection<Long>)` | 批量查询粉丝数，返回 `Map<Long, Long>` |
| `CommentsService` | `getCommentScoresByArticleIds(Collection<Long>)` | 批量查询评论评分（按 ai/user 角色分组），返回 `Map<Long, Map<String, CommentScoreDTO>>` |
| `CategoryService` | `listSubCategoriesByIds(Collection<Long>)` | 批量查询子分类，返回 `Flux<SubCategory>` |

### 3.4 实现注意事项

1. **评论评分查询** (`CommentsServiceImpl.getCommentScoresByArticleIds`)：
   - 与 gozero 原来的 `COMMENT_RATING_QUERY` SQL 逻辑保持一致：按 `star > 0` 过滤，通过 `user.role` 区分 ai/user 角色分组
   - 使用 R2dbcEntityTemplate 逐文章查询，因为 R2DBC 不支持复杂 JOIN + GROUP BY 的派生查询

2. **点赞/收藏/粉丝批量查询**：
   - 由于 ReactiveCrudRepository 不支持 `IN` + `GROUP BY` 的派生查询方法，采用 `Flux.fromIterable().flatMap().collectMap()` 逐 ID 查询后聚合
   - 对于高并发场景，可考虑后续改为自定义 `@Query` 注解的批量 SQL

3. **CategoryController** 新增接口需要额外引入 `jakarta.validation.Valid`，因为原 Controller 使用的是 `@Validated`（Spring 的），而 `@Valid`（Jakarta 的）用于 `@RequestBody` 校验

## 四、gozero 改动详情

### 4.1 新增文件

| 文件 | 说明 |
|------|------|
| `internal/client/springClient/springClient.go` | Spring 远程调用客户端，封装 11 个内部接口 |
| `internal/client/springClient/types.go` | 响应数据解析工具（泛型 `parseData`）+ VO 类型定义 |

### 4.2 SpringClient 接口清单

```go
// 分页获取已发布文章
GetPublishedArticles(ctx, page, size int) (Result, error)

// 批量查询
GetArticleViewsByIDs(ctx, ids []int64) (Result, error)
GetArticlesByIDs(ctx, ids []int64) (Result, error)
GetUserByID(ctx, id int64) (Result, error)
GetUsersByIDs(ctx, ids []int64) (Result, error)
GetCommentScoresByArticleIDs(ctx, ids []int64) (Result, error)
GetLikeCountsByArticleIDs(ctx, ids []int64) (Result, error)
GetCollectCountsByArticleIDs(ctx, ids []int64) (Result, error)
GetFollowCountsByUserIDs(ctx, ids []int64) (Result, error)
GetCategoriesByIDs(ctx, ids []int64) (Result, error)
GetSubCategoriesByIDs(ctx, ids []int64) (Result, error)
```

### 4.3 响应解析工具 (types.go)

使用 Go 1.18 泛型实现通用的 `parseData[T any]` 函数，从 `client.Result.Data`（`any` 类型）中安全解析出目标类型：

```go
func parseData[T any](result client.Result) (T, error)
```

同时提供以下具名解析函数：
- `ParseArticlePage` — 解析分页文章列表
- `ParseArticleViewsMap` — 解析 `map[int64]int`（阅读量）
- `ParseUserVO` / `ParseUserVOs` — 解析单个/批量用户
- `ParseCommentScoresMap` — 解析 `map[int64]map[string]CommentScoreVO`
- `ParseCountsMap` — 解析 `map[int64]int64`（点赞/收藏/粉丝数通用）
- `ParseCategoryVOs` / `ParseSubCategoryVOs` — 解析分类/子分类

### 4.4 改造的核心文件

#### 4.4.1 esSyncerTask.go（完全重写）

**改造前**：通过 `svcCtx.ArticlesModel.IteratePublishedArticles` 直接遍历 MySQL，通过 8 个 Model 查询关联数据。

**改造后**：
1. 通过 `SpringClient.GetPublishedArticles` 分页遍历已发布文章
2. 通过 `SpringClient.GetUsersByIDs` 批量补齐用户名
3. 通过 `SpringClient.GetSubCategoriesByIDs` + `GetCategoriesByIDs` 批量补齐分类名
4. 通过 `SpringClient.GetCommentScoresByArticleIDs` 批量查询评论评分
5. 通过 `SpringClient.GetLikeCountsByArticleIDs` 批量查询点赞数
6. 通过 `SpringClient.GetCollectCountsByArticleIDs` 批量查询收藏数
7. 通过 `SpringClient.GetFollowCountsByUserIDs` 批量查询粉丝数

**注意点**：
- 保留了本地 `userMap`、`categoryMap`、`subCategoryMap` 缓存，避免同一批次内重复远程调用
- 分页循环中通过 `page * batchSize >= total` 判断是否还有下一页
- 四个统计接口（评论/点赞/收藏/粉丝）是顺序调用而非并行，因为 gozero 的 `ServiceDiscovery` 基于 Nacos + 熔断器，并行调用需要额外处理 context 传递

#### 4.4.2 es.go（SearchModel 搜索）

**改造前**：通过 `m.articlesModel`、`m.likesModel`、`m.collectsModel`、`m.focusModel` 四个 Model 接口查询。

**改造后**：全部改为通过 `m.springClient` 远程调用，解析逻辑不变。

#### 4.4.3 types.go（SearchModel 类型定义）

**改造前**：定义了 `ArticleViewCounter`、`LikeCounter`、`CollectCounter`、`FollowCounter` 四个接口，`SearchModelDeps` 依赖这些接口。

**改造后**：移除四个接口，`SearchModelDeps` 直接依赖 `*springClient.SpringClient`，`searchModel` 结构体也相应简化。

### 4.5 上下文和初始化改动

| 文件 | 改动 |
|------|------|
| `contextTypes.go` | `ModelContext` 只保留 `AiHistoryModel`、`ChatMessagesModel`、`SearchModel`；`ClientContext` 新增 `SpringClient` |
| `modelContext.go` | 只初始化 chatMessages、aiHistory 和 SearchModel（传入 SpringClient） |
| `serviceComponentsContext.go` | 新增 `SpringClient` 创建，提取公共 `remoteCallCfg` 变量 |
| `serviceContext.go` | 调整初始化顺序：先创建 `clientCtx`，再传给 `newModelContext` |

### 4.6 删除的文件

**Model 目录（9 个）**：
- `model/articles/` — articlesModel.go + articlesModel_gen.go
- `model/user/` — userModel.go + userModel_gen.go
- `model/category/` — categoryModel.go + categoryModel_gen.go
- `model/categoryReference/` — categoryReferenceModel.go + categoryReferenceModel_gen.go
- `model/collects/` — collectsModel.go + collectsModel_gen.go
- `model/comments/` — commentsModel.go + commentsModel_gen.go
- `model/focus/` — focusModel.go + focusModel_gen.go
- `model/likes/` — likesModel.go + likesModel_gen.go
- `model/subCategory/` — subCategoryModel.go + subCategoryModel_gen.go

**SQL 脚本（9 个）**：
- `script/sql/articles.sql`
- `script/sql/user.sql`
- `script/sql/category.sql`
- `script/sql/category_reference.sql`
- `script/sql/collects.sql`
- `script/sql/comments.sql`
- `script/sql/focus.sql`
- `script/sql/likes.sql`
- `script/sql/sub_category.sql`

删除 SQL 脚本的目的是防止 `goctl` 根据脚本再次生成对应的 model 代码。

## 五、保留的内容

| 内容 | 所属服务 | 说明 |
|------|---------|------|
| `model/chatMessages/` | gozero | 聊天消息表，gozero 专门维护 |
| `model/aiHistory/` | gozero | AI 历史记录，FastAPI 维护，gozero 保留 model 备用 |
| `model/search/` | gozero | ES 搜索模型，不涉及 MySQL |
| `script/sql/chat_messages.sql` | gozero | 聊天消息 DDL |
| `script/sql/ai_history.sql` | gozero | AI 历史 DDL |
| `infrastructureContext.go` 中的 `initSqlx` | gozero | MySQL 连接保留，用于 chat_messages 表 |

## 六、后续建议

### 6.1 性能优化

1. **批量查询改为单次 SQL**：当前点赞/收藏/粉丝的批量查询使用 `Flux.flatMap` 逐 ID 查询，在 ID 数量较大时会产生 N 次 SQL。建议后续在 Repository 中添加自定义 `@Query` 实现真正的 `GROUP BY` 批量查询：
   ```java
   @Query("SELECT article_id, COUNT(*) as cnt FROM article_likes WHERE article_id IN (:ids) GROUP BY article_id")
   Flux<IdCount> countByArticleIdIn(@Param("ids") Collection<Long> ids);
   ```

2. **esSyncerTask 并行调用**：四个统计接口（评论/点赞/收藏/粉丝）可以改为 goroutine 并行调用，减少同步等待时间。

### 6.2 可观测性

1. 在 Spring 内部接口上增加耗时监控，便于排查远程调用瓶颈
2. 在 gozero SpringClient 层增加调用链追踪（OpenTelemetry / Jaeger）

### 6.3 容错

1. 当前 esSyncerTask 中远程调用失败会直接返回 error 中断同步。可考虑增加降级策略：单个接口失败时使用空数据继续，记录告警日志
2. SearchModel 中的远程调用同样可以增加降级：查询失败时 views/likes/collects/follows 使用默认值 0

### 6.4 清理

1. `infrastructureContext.go` 中的 `initChatMessagesTable` 仍然通过 MySQL 直连建表，如果后续 chat_messages 也迁移到其他服务，可以一并移除 MySQL 连接
2. `model/aiHistory/` 目录当前未被任何逻辑代码使用，如果确认不需要可移除

### 6.5 配置

确保 `gozero` 的 Nacos 配置中包含 `spring` 服务的注册信息，否则 SpringClient 无法通过服务发现找到 Spring 实例。