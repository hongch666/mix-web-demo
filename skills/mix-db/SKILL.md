---
name: mix-db
description: mix-web-demo 仓库数据库与索引设计专项规范，覆盖 MySQL/MongoDB/ClickHouse/ES/pgvector 的建表位置、索引登记、设计约束与验证方法。涉及建表、查询、索引变更时加载
---

# mix-db 数据库与索引设计

## 数据库与索引设计（全部存储）

**新增表、新增或修改查询时，必须在同一次改动里给出索引方案**：索引按真实的 `WHERE` / `JOIN` / `ORDER BY` / `GROUP BY` 设计，等值过滤列在前、范围与排序列在后，能覆盖查询时优先覆盖索引；没有查询依据的索引不建。已有复合索引左前缀能覆盖的单列索引要一并删除，避免重复写入开销。

索引写在哪里取决于建表方式，两类存储的约定不同。

### 手写 DDL（索引内联，服务启动不补索引）

| 服务                | 建表与索引位置                                                                                             |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| Spring              | `spring/.../common/constants/Scripts.java` 的 `CREATE_*_TABLE`，同步 `db/mysql/spring/*.sql`               |
| GoZero              | `gozero/app/common/constants/scripts.go` 的 `CREATE_CHAT_MESSAGES_TABLE_SQL`，同步 `db/mysql/gozero/*.sql` |
| ClickHouse 兜底脚本 | `db/clickhouse/**/*.sql` 的 `ORDER BY` / `PARTITION BY` / 跳数 `INDEX` / `TTL`                             |

- 索引直接写在 `CREATE TABLE` 里（`KEY` / `INDEX` / 跳数 `INDEX`），**不要再写启动期 `ALTER TABLE ADD INDEX` 逻辑**：项目已刻意移除该逻辑，表已存在时启动不会修改索引，索引不一致由运维处理
- 改了索引必须同步 `db/mysql/**` / `db/clickhouse/**` 里对应的脚本，这是同一份 DDL 的第二处来源

### 框架建表（索引单独登记与创建）

| 存储               | 登记位置                                                                             | 说明                                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| FastAPI MySQL      | `fastapi/app/core/constants/indexes.py` → `MySQLIndexes`                             | SQLAlchemy `create_all` 不建业务索引，启动由 `create_mysql_indexes_async()` 按 `information_schema` 补齐            |
| FastAPI ClickHouse | 同文件 → `ClickHouseIndexes`                                                         | 跳数索引与 TTL 只能 `ALTER`；改 `ORDER BY` / `PARTITION BY` 要同步 `warehouse/base.py` 的 `WAREHOUSE_ENGINE_CONFIG` |
| FastAPI pgvector   | 同文件 → `PostgreSQLIndexes`                                                         | 表由 LangChain 创建；ANN 索引要求 `embedding` 列声明维度                                                            |
| NestJS MongoDB     | `*.schema.ts` 的 `Schema.index()` + service 的 `requiredIndexes` + `db/mongodb/*.js` | 三处必须同名同列，否则出现重复索引或 `IndexOptionsConflict`                                                         |
| GoZero ES          | `db/es/init.es` 与 `gozero/app/common/constants/scripts.go` 的 `ES_INDEX_MAPPING`    | 两处保持一致；字段类型不可原地修改，变更需重建索引                                                                  |

### 各存储的设计约束

- **MySQL**：避免 `%LIKE%`（B-tree 结构性无效）；`ORDER BY` 列要进索引，否则 filesort；列表接口避免 `SELECT *` 带出 `LONGTEXT`
- **MongoDB**：`sort` 字段必须进复合索引，否则退化为内存排序；`$regex` 只有前缀锚定 `^kw` 能用索引；深分页用 `_id` 游标而不是 `skip`
- **ClickHouse**：`ReplacingMergeTree` 的 `ORDER BY` 就是去重键，**不能为了查询把 `event_id` 移出排序键**；查询侧写分区谓词（`action_date >= toDate(...)`，不要 `toString(toYYYYMM(...)) = ...` 这种函数包裹），再配合跳数索引；高频聚合考虑物化视图或预聚合表
- **Elasticsearch**：过滤用 `keyword` + `term`，全文检索用 `text` 分词；`text` 不能聚合与排序；避免前后通配 `*kw*`
- **pgvector**：检索算子必须与索引 ops 匹配（余弦 `<=>` 对应 `vector_cosine_ops`）

### 改完索引的验证

- MySQL：`EXPLAIN` 确认不再出现 `Using filesort` / `Using temporary`
- MongoDB：`explain("executionStats")` 确认 `totalKeysExamined ≈ nReturned` 且无 `SORT` 阶段
- ClickHouse：`EXPLAIN indexes = 1` 看 Granules 的裁剪比例
- Elasticsearch / pgvector：`profile: true`、`EXPLAIN (ANALYZE, BUFFERS)` 确认命中索引

完整清单与迁移步骤见根目录《索引优化执行手册.md》
