/**
 * MongoDB 索引信息结构，仅包含索引名
 *
 * 日志类服务启动校验索引时共用，避免各模块重复声明同名字段
 */
export interface MongoIndexInfo {
  /** 索引名 */
  name?: string;
}
