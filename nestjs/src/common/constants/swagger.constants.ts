/**
 * Swagger/OpenAPI 配置常量
 */
export class SwaggerConfig {
  static readonly SWAGGER_TITLE = "NestJS部分的Swagger文档";
  static readonly SWAGGER_DESCRIPTION = "这是项目的NestJS部分的Swagger文档";
  static readonly SWAGGER_VERSION = "1.0.0";
  static readonly SWAGGER_PATH = "api-docs";
  static readonly SWAGGER_TAGS: [string, string][] = [
    ["API日志模块", "API日志相关API，包括日志查询、统计等功能"],
    ["文章日志模块", "文章操作日志相关API，包括日志记录、查询、清理等"],
    ["测试模块", "服务测试相关API，用于验证各个微服务是否正常运行"],
    ["文件上传", "文件上传相关API，包括本地文件上传、图片上传、PDF上传等"],
    ["下载模块", "文件下载相关API，包括Word下载、PDF下载等"],
    [
      "GitHub 登录模块",
      "GitHub 授权与操作相关API，包括授权登录、用户信息获取等",
    ],
    ["邮件模块", "邮件发送相关API，包括验证码邮件、通知邮件等"],
    [
      "MongoDB工具模块",
      "MongoDB 日志查询工具相关API，仅限白名单内集合的只读查询",
    ],
    ["定时任务模块", "定时任务相关API，包括任务的查询、手动触发、启停等操作"],
    ["表格列设置", "用户表格列配置相关API，包括列配置的查询、保存与删除"],
    ["SQL工具", "SQL 执行工具相关API，用于安全的数据库查询与操作"],
  ];
}
