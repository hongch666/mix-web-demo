/**
 * SQL 工具常量 — 表名白名单、只读前缀白名单、正则、SQL模板、查询限制等
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
  /** 用于移除 SQL 字符串字面量，避免字符串内的 ; 被误判 */
  static readonly SQL_STRING_LITERAL_REGEX = /'[^']*'|"[^"]*"/g;
  /** 用于移除末尾分号 */
  static readonly SQL_TRAILING_SEMICOLON_REGEX = /;\s*$/;
  /** 空白字符标准化 */
  static readonly SQL_WHITESPACE_REGEX = /\s+/g;

  // ===== SQL 查询最大返回行数（LIMIT 上限） =====
  static readonly MAX_LIMIT = 100;

  // ===== SQL 模板函数 =====
  static readonly SHOW_COLUMNS_SQL = (tableName: string): string =>
    `SHOW COLUMNS FROM \`${tableName}\``;

  static readonly COUNT_ROWS_SQL = (tableName: string): string =>
    `SELECT COUNT(*) AS cnt FROM \`${tableName}\` WHERE 1 LIMIT 1`;
}
