/**
 * HTTP 请求头名称常量 — 区分出站规范大小写与 Fastify 入站小写键
 */
export class HeaderNames {
  // ===== 出站请求头名称 =====

  /** 出站请求头中的用户 ID */
  static readonly USER_ID = "X-User-Id";

  /** 出站请求头中的用户名 */
  static readonly USERNAME = "X-Username";

  /** 出站请求头中的会话 ID */
  static readonly SESSION_ID = "X-Session-Id";

  /** 出站请求头中的授权令牌 */
  static readonly AUTHORIZATION = "Authorization";

  /** 出站请求头中的内部服务令牌 */
  static readonly INTERNAL_TOKEN = "X-Internal-Token";

  // ===== 入站请求头名称 =====

  /** Fastify 规范化后的用户 ID 请求头键 */
  static readonly USER_ID_LOWER = "x-user-id";

  /** Fastify 规范化后的用户名请求头键 */
  static readonly USERNAME_LOWER = "x-username";

  /** Fastify 规范化后的会话 ID 请求头键 */
  static readonly SESSION_ID_LOWER = "x-session-id";

  /** Fastify 规范化后的授权令牌请求头键 */
  static readonly AUTHORIZATION_LOWER = "authorization";

  /** Fastify 规范化后的内部服务令牌请求头键 */
  static readonly INTERNAL_TOKEN_LOWER = "x-internal-token";

  // ===== 令牌前缀 =====

  /** Bearer 令牌前缀，含尾部空格 */
  static readonly BEARER_PREFIX = "Bearer ";
}
