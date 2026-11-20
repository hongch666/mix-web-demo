/**
 * 文章导出元信息 — Word、PDF、Markdown 三种格式共用的字段集合
 *
 * 由下载服务按远程文章数据构造后交给 ExportTemplate 渲染，三种格式取值一致，避免同一篇文章导出结果不同
 */
export interface ArticleExportMeta {
  /** 文章编号 */
  id: number;
  /** 文章标题 */
  title: string;
  /** 作者名，缺失时为未知用户 */
  author: string;
  /** 分类路径，父分类与子分类以 / 连接，缺失时为未分类 */
  category: string;
  /** 发布状态文案 */
  status: string;
  /** 已拆分并去空的标签列表 */
  tags: string[];
  /** 浏览量 */
  views: number;
  /** 创作时间，缺失时为占位符 */
  createTime: string;
  /** 更新时间，缺失时为占位符 */
  updateTime: string;
}
