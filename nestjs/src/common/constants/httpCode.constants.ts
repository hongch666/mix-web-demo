/**
 * HTTP 状态码常量 - 与 HTTP 响应状态码一致，同时作为响应体中的 code 字段值
 */
export class HttpCode {
  // ===== HTTP 状态码 =====

  /** 请求成功 */
  static readonly OK = 200;
  /** 资源已临时移动，用于重定向 */
  static readonly FOUND = 302;
  /** 参数或请求体不合法 */
  static readonly BAD_REQUEST = 400;
  /** 未认证或令牌失效 */
  static readonly UNAUTHORIZED = 401;
  /** 已认证但无权限 */
  static readonly FORBIDDEN = 403;
  /** 资源不存在 */
  static readonly NOT_FOUND = 404;
  /** 资源状态冲突 */
  static readonly CONFLICT = 409;
  /** 参数语义校验不通过 */
  static readonly UNPROCESSABLE_ENTITY = 422;
  /** 服务内部异常 */
  static readonly INTERNAL_SERVER_ERROR = 500;
  /** 下游服务返回异常 */
  static readonly BAD_GATEWAY = 502;
  /** 依赖缺失导致服务不可用 */
  static readonly SERVICE_UNAVAILABLE = 503;
  /** 下游调用超时 */
  static readonly GATEWAY_TIMEOUT = 504;
}
