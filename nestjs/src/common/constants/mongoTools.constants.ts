/**
 * MongoDB 工具常量 — collection 白名单、危险操作符黑名单、聚合阶段白名单
 */
export class MongoTools {
  // ===== 集合与操作符白名单 =====

  // ===== 允许查询的 collection 白名单（仅开放日志相关集合） =====

  /** MongoDB 工具允许访问的集合白名单 */
  static readonly ALLOWED_COLLECTIONS = new Set<string>([
    "apilogs",
    "articlelogs",
  ]);

  // ===== 禁止使用的 MongoDB 危险操作符（防止任意代码执行或高开销查询） =====

  /** 禁止在查询条件中出现的操作符 */
  static readonly FORBIDDEN_OPERATORS = new Set<string>([
    "$where",
    "$function",
    "$accumulator",
    "$expr",
  ]);

  // ===== 聚合阶段限制 =====

  // ===== 允许使用的聚合阶段白名单 =====

  // 只开放只读分析阶段，$out / $merge / $lookup / $graphLookup / $facet 等
  // 会写数据、跨集合访问或放大开销的阶段一律不开放
  /** 允许的聚合阶段白名单，需与 FastAPI 侧 MONGODB_AGGREGATE_STAGES 一致 */
  static readonly ALLOWED_AGGREGATE_STAGES = new Set<string>([
    "$match",
    "$project",
    "$addFields",
    "$group",
    "$sort",
    "$limit",
    "$count",
    "$unwind",
  ]);

  // ===== 单个 pipeline 允许的最大阶段数 =====

  /** 聚合管道的阶段数上限 */
  static readonly MAX_PIPELINE_STAGES = 6;

  // ===== 聚合结果最大返回文档数（服务端强制追加 $limit） =====

  /** 聚合查询返回的文档数上限 */
  static readonly MAX_AGGREGATE_DOCS = 100;

  // ===== 聚合查询最长执行时间（毫秒），防止大集合聚合拖垮日志库 =====

  /** 聚合查询的执行超时毫秒数 */
  static readonly AGGREGATE_MAX_TIME_MS = 5000;
}
