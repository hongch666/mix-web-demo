/**
 * 错误标识常量 — 传给 BusinessException 的 error 参数
 */
export class ErrorIds {
  // ===== 400 Bad Request =====
  static readonly PARAM_PARSE_FAILED = "PARAM_PARSE_FAILED";

  // ===== 401 Unauthorized =====
  static readonly INTERNAL_TOKEN_MISSING_ERROR = "INTERNAL_TOKEN_MISSING";
  static readonly INTERNAL_TOKEN_INVALID_ERROR = "INTERNAL_TOKEN_INVALID";
  static readonly INTERNAL_TOKEN_EXPIRED_ERROR = "INTERNAL_TOKEN_EXPIRED";

  // ===== 403 Forbidden =====
  static readonly UNAUTHORIZED_USER_ERROR = "UNAUTHORIZED_USER";
  static readonly NO_ADMIN_PERMISSION = "NO_ADMIN_PERMISSION";
  static readonly INTERNAL_TOKEN_SERVICE_MISMATCH =
    "INTERNAL_TOKEN_SERVICE_MISMATCH";

  // ===== 404 Not Found =====
  static readonly ARTICLE_NOT_FOUND = "ARTICLE_NOT_FOUND";
  static readonly EMPTY_FILE_PATH = "EMPTY_FILE_PATH";

  // ===== 500 Internal Server Error =====
  static readonly NESTJS_SERVER_ERROR = "NESTJS_SERVER_ERROR";
  static readonly OSS_UPLOAD_ERROR = "OSS_UPLOAD_ERROR";
  static readonly INTERNAL_TOKEN_SECRET_NOT_NULL =
    "INTERNAL_TOKEN_SECRET_NOT_NULL";

  // ===== 502 Bad Gateway =====
  static readonly SERVICE_CALL_FAILED = "SERVICE_CALL_FAILED";
  static readonly GITHUB_ACCESS_TOKEN_FAILED = "GITHUB_ACCESS_TOKEN_FAILED";
  static readonly GITHUB_USER_PROFILE_FAILED = "GITHUB_USER_PROFILE_FAILED";
  static readonly GITHUB_USER_PROFILE_INVALID = "GITHUB_USER_PROFILE_INVALID";
  static readonly GITHUB_TOKEN_TICKET_FAILED = "GITHUB_TOKEN_TICKET_FAILED";

  // ===== 503 Service Unavailable =====
  static readonly NO_AVAILABLE_SERVICE_INSTANCE =
    "NO_AVAILABLE_SERVICE_INSTANCE";
}
