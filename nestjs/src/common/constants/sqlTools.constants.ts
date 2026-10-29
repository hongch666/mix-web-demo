/**
 * SQL 工具常量 — 表名白名单、只读前缀白名单、正则、SQL模板、查询限制等
 */
export class SqlTools {
  // ===== SQL 模板 =====

  // ===== SQL 模板函数 =====

  /** 查询表结构的 SQL 模板，表名来自白名单 */
  static readonly SHOW_COLUMNS_SQL = (tableName: string): string =>
    `SHOW COLUMNS FROM \`${tableName}\``;

  /** 统计表行数的 SQL 模板，表名来自白名单 */
  static readonly COUNT_ROWS_SQL = (tableName: string): string =>
    `SELECT COUNT(*) AS cnt FROM \`${tableName}\` WHERE 1 LIMIT 1`;

  // ===== 白名单与限制 =====

  // ===== 表名白名单（仅开放 NestJS 自管的表） =====

  /** SQL 工具允许访问的表名白名单 */
  static readonly TABLE_WHITELIST = new Set<string>(["user_table_settings"]);

  // ===== 只读语句前缀白名单 =====

  /** 只读语句前缀白名单 */
  static readonly ALLOWED_PREFIXES = [
    "SELECT",
    "WITH",
    "SHOW",
    "DESC",
    "DESCRIBE",
    "EXPLAIN",
  ];

  // ===== 解析正则 =====

  // ===== 正则 =====

  /** 提取 FROM / JOIN 后的表名 */
  static readonly TABLE_NAME_REGEX = /\b(?:FROM|JOIN)\s+`?(\w+)`?/gi;
  /** 提取 LIMIT 后的行数 */
  static readonly LIMIT_REGEX = /\bLIMIT\s+(\d+)/i;
  /** 提取命名参数 */
  static readonly NAMED_PARAM_REGEX = /:(\w+)/g;
  /** 用于移除 SQL 字符串字面量，避免字符串内的 ; 被误判 */
  /** 匹配 SQL 字符串字面量，避免其中的分号被误判 */
  static readonly SQL_STRING_LITERAL_REGEX = /'[^']*'|"[^"]*"/g;
  /** 用于移除末尾分号 */
  /** 匹配语句末尾的分号 */
  static readonly SQL_TRAILING_SEMICOLON_REGEX = /;\s*$/;
  /** 空白字符标准化 */
  /** 归一化连续空白字符 */
  static readonly SQL_WHITESPACE_REGEX = /\s+/g;

  // ===== SQL 查询最大返回行数（LIMIT 上限） =====

  /** SQL 查询允许的最大返回行数 */
  static readonly MAX_LIMIT = 100;
}
