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
  static readonly ARTICLE_LOG_NOT_FOUND_ERROR = "ARTICLE_LOG_NOT_FOUND";
  static readonly ARTICLE_LOG_PARTIAL_NOT_FOUND_ERROR =
    "ARTICLE_LOG_PARTIAL_NOT_FOUND";
  static readonly API_LOG_NOT_FOUND_ERROR = "API_LOG_NOT_FOUND";
  static readonly API_LOG_PARTIAL_NOT_FOUND_ERROR = "API_LOG_PARTIAL_NOT_FOUND";
  static readonly FILE_PART_NOT_FOUND_ERROR = "FILE_PART_NOT_FOUND";

  // ===== 422 Unprocessable Entity =====
  static readonly ONLY_PDF_SUPPORTED_ERROR = "ONLY_PDF_SUPPORTED";
  static readonly NO_FILE_UPLOADED_ERROR = "NO_FILE_UPLOADED";
  static readonly FILE_NO_VALID_METHOD_ERROR = "FILE_NO_VALID_METHOD";

  // ===== 500 Internal Server Error =====
  static readonly NESTJS_SERVER_ERROR = "NESTJS_SERVER_ERROR";
  static readonly OSS_UPLOAD_ERROR = "OSS_UPLOAD_ERROR";

  // ===== 502 Bad Gateway =====
  static readonly SERVICE_CALL_FAILED = "SERVICE_CALL_FAILED";

  // ===== 503 Service Unavailable =====
  static readonly OSS_CLIENT_NOT_INITIALIZED_ERROR =
    "OSS_CLIENT_NOT_INITIALIZED";
  static readonly SERVICE_DISCOVERY_FAILED = "SERVICE_DISCOVERY_FAILED";
  static readonly NO_AVAILABLE_SERVICE_INSTANCE =
    "NO_AVAILABLE_SERVICE_INSTANCE";

  // ===== 504 Gateway Timeout =====
  static readonly OSS_PUT_TIMEOUT = "OSS_PUT_TIMEOUT";
}
