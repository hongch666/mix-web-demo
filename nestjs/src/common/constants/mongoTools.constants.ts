/**
 * MongoDB 工具常量 — collection 白名单、危险操作符黑名单
 */
export class MongoTools {
  // ===== 允许查询的 collection 白名单（仅开放日志相关集合） =====
  static readonly ALLOWED_COLLECTIONS = new Set<string>([
    "apilogs",
    "articlelogs",
  ]);

  // ===== 禁止使用的 MongoDB 危险操作符（防止任意代码执行或高开销查询） =====
  static readonly FORBIDDEN_OPERATORS = new Set<string>([
    "$where",
    "$function",
    "$accumulator",
    "$expr",
  ]);
}
