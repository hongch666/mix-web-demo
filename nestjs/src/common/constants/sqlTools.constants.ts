/**
 * SQL 工具常量 — 表名白名单、只读前缀白名单、正则、查询限制等
 */
export class SqlTools {
  // ===== 表名白名单（仅开放 NestJS 自管的表） =====
  static readonly TABLE_WHITELIST = new Set<string>(["user_table_settings"]);

  // ===== 只读语句前缀白名单 =====
  static readonly ALLOWED_PREFIXES = [
    "SELECT",
    "WITH",
    "SHOW",
    "DESC",
    "DESCRIBE",
    "EXPLAIN",
  ];

  // ===== 正则 =====
  static readonly TABLE_NAME_REGEX = /\b(?:FROM|JOIN)\s+`?(\w+)`?/gi;
  static readonly LIMIT_REGEX = /\bLIMIT\s+(\d+)/i;
  static readonly NAMED_PARAM_REGEX = /:(\w+)/g;

  // ===== SQL 查询最大返回行数（LIMIT 上限） =====
  static readonly MAX_LIMIT = 100;
}
