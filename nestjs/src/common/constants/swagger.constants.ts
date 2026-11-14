/**
 * Swagger/OpenAPI 配置常量
 */
export class SwaggerConfig {
  // ===== 文档基础信息 =====

  /** 文档标题 */
  static readonly SWAGGER_TITLE = "NestJS部分的Swagger文档";
  /** 文档描述：服务定位、统一响应、命名与认证约定，展示在 Apifox 项目文档页顶部 */
  static readonly SWAGGER_DESCRIPTION = [
    "**服务职责**：文章操作日志与 API 日志的查询分析、Word/PDF 下载、文件上传、GitHub OAuth 回调、邮件发送、MongoDB 与 SQL 只读工具、定时任务管理、用户表格列设置；对外统一经 APISIX 网关（8080）访问。",
    "",
    '**统一响应**：除 OAuth 重定向类接口外，所有接口返回 `{"code": 200, "msg": "...", "data": ...}`，code 与 HTTP 状态码一致；无返回数据的接口 data 为 null。',
    "",
    "**字段命名**：路径参数、查询参数与响应字段统一 snake_case，并与路由声明保持一致。",
    "",
    "**认证方式**：需登录的接口由网关透传的用户身份校验，未登录或令牌失效返回 401；服务间调用使用 X-Internal-Token 请求头。",
    "",
    "**文档来源**：@nestjs/swagger 从控制器与 DTO 生成（OpenAPI 3.1），内联请求与响应在构建阶段提升为 components.schemas 下以 Nestjs 开头的具名模型。",
  ].join("\n");
  /** 接口版本号 */
  static readonly SWAGGER_VERSION = "1.0.0";
  /** 产物的 OpenAPI 规范版本，3.1 才能表达空值响应 */
  static readonly OPENAPI_VERSION = "3.1.0";
  /** Swagger UI 的挂载路径 */
  static readonly SWAGGER_PATH = "api-docs";
  /** 接口分组标签清单，每项为英文标识与中文名称 */
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
