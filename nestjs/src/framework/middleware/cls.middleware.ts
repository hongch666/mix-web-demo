import { Injectable, NestMiddleware } from "@nestjs/common";
import type { FastifyReply, FastifyRequest } from "fastify";
import { ClsService } from "nestjs-cls";

/**
 * 请求上下文中间件，在 AppModule 中对所有路由生效，将请求头中的用户身份与令牌解析后写入 CLS 上下文
 */
@Injectable()
export class ClsMiddleware implements NestMiddleware {
  constructor(private readonly cls: ClsService) {}

  /**
   * 解析请求头中的用户 ID、用户名、会话 ID 与各类令牌并写入 CLS 上下文，供后续守卫、拦截器与业务逻辑读取
   */
  use(req: FastifyRequest, _res: FastifyReply, next: () => void): void {
    // Fastify 会将所有头部转换为小写，这里统一把 userId 规整成 number 再写入 CLS
    const rawUserId: string | string[] | undefined = req.headers["x-user-id"];
    const rawUsername: string | string[] | undefined =
      req.headers["x-username"];
    const rawSessionId: string | string[] | undefined =
      req.headers["x-session-id"];
    const rawToken: string | string[] | undefined =
      req.headers["authorization"];
    const rawInternalToken: string | string[] | undefined =
      req.headers["x-internal-token"];
    const userId: number | undefined = this.parseUserId(rawUserId);
    const username: string = this.parseUsername(rawUsername);
    const sessionId: string = this.parseSessionId(rawSessionId);
    const token: string = this.extractBearerToken(rawToken);
    const internalToken: string = this.extractBearerToken(rawInternalToken);

    this.cls.set("userId", userId);
    this.cls.set("username", username);
    this.cls.set("sessionId", sessionId);
    this.cls.set("token", token);
    this.cls.set("internalToken", internalToken);
    next();
  }

  /**
   * 将 x-user-id 请求头解析为正整数用户 ID，非法值返回 undefined
   */
  private parseUserId(
    value: string | string[] | undefined,
  ): number | undefined {
    if (Array.isArray(value)) {
      return this.parseUserId(value[0]);
    }

    if (!value) {
      return undefined;
    }

    const userId: number = Number(value);
    return Number.isInteger(userId) && userId > 0 ? userId : undefined;
  }

  /**
   * 取 x-username 请求头的首个值作为用户名，缺省返回空字符串
   */
  private parseUsername(value: string | string[] | undefined): string {
    if (Array.isArray(value)) {
      return value[0] || "";
    }

    return value || "";
  }

  /**
   * 取 x-session-id 请求头的首个值作为会话 ID，缺省返回空字符串
   */
  private parseSessionId(value: string | string[] | undefined): string {
    if (Array.isArray(value)) {
      return value[0] || "";
    }

    return value || "";
  }

  /**
   * 从 authorization 或 x-internal-token 请求头中剥离 Bearer 前缀提取令牌
   */
  private extractBearerToken(value: string | string[] | undefined): string {
    let header: string;
    if (Array.isArray(value)) {
      header = value[0] || "";
    } else {
      header = value || "";
    }
    const bearerPrefix = "Bearer ";
    if (header.startsWith(bearerPrefix)) {
      return header.slice(bearerPrefix.length);
    }
    return "";
  }
}
