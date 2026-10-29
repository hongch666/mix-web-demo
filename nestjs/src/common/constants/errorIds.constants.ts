/**
 * 错误标识常量 — 传给 BusinessException 的 error 参数
 */
export class ErrorIds {
  // ===== 400 Bad Request =====

  /** 错误标识：参数解析失败 */
  static readonly PARAM_PARSE_FAILED = "PARAM_PARSE_FAILED";
  /** 错误标识：目标用户标识非法 */
  static readonly USER_SCOPE_TARGET_INVALID = "USER_SCOPE_TARGET_INVALID";

  // ===== 401 Unauthorized =====

  /** 错误标识：缺少内部令牌 */
  static readonly INTERNAL_TOKEN_MISSING_ERROR = "INTERNAL_TOKEN_MISSING";
  /** 错误标识：内部令牌无效 */
  static readonly INTERNAL_TOKEN_INVALID_ERROR = "INTERNAL_TOKEN_INVALID";
  /** 错误标识：内部令牌已过期 */
  static readonly INTERNAL_TOKEN_EXPIRED_ERROR = "INTERNAL_TOKEN_EXPIRED";

  // ===== 403 Forbidden =====

  /** 错误标识：未认证用户 */
  static readonly UNAUTHORIZED_USER_ERROR = "UNAUTHORIZED_USER";
  /** 错误标识：缺少管理员权限 */
  static readonly NO_ADMIN_PERMISSION = "NO_ADMIN_PERMISSION";
  /** 错误标识：仅本人或管理员可访问 */
  static readonly SELF_OR_ADMIN_REQUIRED = "SELF_OR_ADMIN_REQUIRED";
  /** 错误标识：内部令牌服务名不匹配 */
  static readonly INTERNAL_TOKEN_SERVICE_MISMATCH =
    "INTERNAL_TOKEN_SERVICE_MISMATCH";

  // ===== 404 Not Found =====

  /** 错误标识：文章不存在 */
  static readonly ARTICLE_NOT_FOUND = "ARTICLE_NOT_FOUND";
  /** 错误标识：未传入文件路径 */
  static readonly EMPTY_FILE_PATH = "EMPTY_FILE_PATH";

  // ===== 500 Internal Server Error =====

  /** 错误标识：NestJS 服务内部错误 */
  static readonly NESTJS_SERVER_ERROR = "NESTJS_SERVER_ERROR";
  /** 错误标识：管理员权限校验失败 */
  static readonly ADMIN_PERMISSION_CHECK_FAILED =
    "ADMIN_PERMISSION_CHECK_FAILED";
  /** 错误标识：OSS 上传失败 */
  static readonly OSS_UPLOAD_ERROR = "OSS_UPLOAD_ERROR";
  /** 错误标识：内部令牌密钥未配置 */
  static readonly INTERNAL_TOKEN_SECRET_NOT_NULL =
    "INTERNAL_TOKEN_SECRET_NOT_NULL";

  // ===== 502 Bad Gateway =====

  /** 错误标识：服务调用失败 */
  static readonly SERVICE_CALL_FAILED = "SERVICE_CALL_FAILED";
  /** 错误标识：GitHub 访问令牌获取失败 */
  static readonly GITHUB_ACCESS_TOKEN_FAILED = "GITHUB_ACCESS_TOKEN_FAILED";
  /** 错误标识：GitHub 用户资料获取失败 */
  static readonly GITHUB_USER_PROFILE_FAILED = "GITHUB_USER_PROFILE_FAILED";
  /** 错误标识：GitHub 用户资料不完整 */
  static readonly GITHUB_USER_PROFILE_INVALID = "GITHUB_USER_PROFILE_INVALID";
  /** 错误标识：GitHub 登录票据换取失败 */
  static readonly GITHUB_TOKEN_TICKET_FAILED = "GITHUB_TOKEN_TICKET_FAILED";

  // ===== 503 Service Unavailable =====

  /** 错误标识：没有可用的服务实例 */
  static readonly NO_AVAILABLE_SERVICE_INSTANCE =
    "NO_AVAILABLE_SERVICE_INSTANCE";

  // ===== MongoDB 工具 =====

  /** 错误标识：MongoDB 集合不在白名单 */
  static readonly MONGO_COLLECTION_NOT_ALLOWED = "MONGO_COLLECTION_NOT_ALLOWED";
  /** 错误标识：使用了禁用的查询操作符 */
  static readonly MONGO_FORBIDDEN_OPERATOR = "MONGO_FORBIDDEN_OPERATOR";
}
