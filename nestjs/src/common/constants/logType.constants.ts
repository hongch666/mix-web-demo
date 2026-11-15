/**
 * 日志类型常量 — 删除墓碑的日志类型标识，与数仓 ODS 表一一对应
 */
export class LogTypes {
  // ===== 日志类型 =====

  /** API 日志类型标识，对应数仓 ods_api_log */
  static readonly API = "api";

  /** 文章操作日志类型标识，对应数仓 ods_article_log */
  static readonly ARTICLE = "article";
}
