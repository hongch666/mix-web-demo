import { CanActivate, ExecutionContext, Injectable } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import type { FastifyRequest } from "fastify";
import { ClsService } from "nestjs-cls";
import { ErrorIds, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { SpringClientService } from "src/module/common/client/springClient.service";
import { LoggerService } from "src/module/common/logger/logger.service";
import {
  REQUIRE_SELF_KEY,
  REQUIRE_SELF_OPTIONS_KEY,
  type RequireSelfOptions,
} from "../decorators/requireSelf.decorator";

/**
 * 本人或管理员访问守卫，通过 APP_GUARD 全局注册
 * 对标注 @RequireSelf 的接口解析目标用户标识，非本人时要求管理员权限
 */
@Injectable()
export class RequireSelfGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly cls: ClsService,
    private readonly springClient: SpringClientService,
    private readonly logger: LoggerService,
  ) {}

  /**
   * 解析目标用户并判断当前登录用户是否为目标用户本人或管理员
   */
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requireSelf: boolean | undefined =
      this.reflector.getAllAndOverride<boolean>(REQUIRE_SELF_KEY, [
        context.getHandler(),
        context.getClass(),
      ]);

    if (!requireSelf) {
      return true;
    }

    const currentUserId: number | undefined = this.cls.get<number>("userId");
    if (!currentUserId) {
      this.logger.warning(Messages.USER_IDENTITY_MISSING);
      throw BusinessException.unauthorized(
        Messages.UNAUTHORIZED_USER,
        ErrorIds.UNAUTHORIZED_USER_ERROR,
      );
    }

    const options: RequireSelfOptions =
      this.reflector.getAllAndOverride<RequireSelfOptions>(
        REQUIRE_SELF_OPTIONS_KEY,
        [context.getHandler(), context.getClass()],
      ) ?? {};
    const request: FastifyRequest = context.switchToHttp().getRequest();
    const targetUserId: number = this.resolveTargetUserId(
      request,
      options,
      currentUserId,
    );

    // 访问本人数据不额外查询角色，避免常规路径多一次远程调用
    if (targetUserId === currentUserId) {
      return true;
    }

    const isAdmin: boolean = await this.checkAdmin(currentUserId);
    if (!isAdmin) {
      this.logger.warning(
        Messages.USER_SCOPE_DENIED(currentUserId, targetUserId),
      );
      throw BusinessException.forbidden(
        Messages.SELF_OR_ADMIN_REQUIRED,
        ErrorIds.SELF_OR_ADMIN_REQUIRED,
      );
    }

    this.logger.info(
      Messages.USER_SCOPE_ADMIN_ACCESS(currentUserId, targetUserId),
    );
    return true;
  }

  /**
   * 按装饰器配置从查询参数、路径参数或请求体中解析目标用户 ID，缺省回退为当前登录用户
   */
  private resolveTargetUserId(
    request: FastifyRequest,
    options: RequireSelfOptions,
    currentUserId: number,
  ): number {
    const source: string = options.source ?? "query";
    const paramName: string = options.paramName ?? "user_id";
    const container: Record<string, unknown> | undefined =
      this.pickParamContainer(request, source);

    if (!container) {
      return currentUserId;
    }

    const rawValue: unknown = container[paramName];
    if (rawValue === undefined || rawValue === null || rawValue === "") {
      return currentUserId;
    }

    return this.parseTargetUserId(
      Array.isArray(rawValue) ? rawValue[0] : rawValue,
    );
  }

  /**
   * 按来源取出承载目标用户标识的参数集合
   */
  private pickParamContainer(
    request: FastifyRequest,
    source: string,
  ): Record<string, unknown> | undefined {
    switch (source) {
      case "param":
        return request.params as Record<string, unknown> | undefined;
      case "body":
        return request.body as Record<string, unknown> | undefined;
      default:
        return request.query as Record<string, unknown> | undefined;
    }
  }

  /**
   * 将目标用户标识转换为正整数，非法值抛出 400 业务异常
   */
  private parseTargetUserId(value: unknown): number {
    const targetUserId: number = Number(value);
    if (!Number.isInteger(targetUserId) || targetUserId <= 0) {
      throw BusinessException.badRequest(
        Messages.USER_SCOPE_TARGET_INVALID,
        ErrorIds.USER_SCOPE_TARGET_INVALID,
      );
    }
    return targetUserId;
  }

  /**
   * 调用 Spring 服务判定当前用户是否管理员，查询失败按 fail-closed 处理
   */
  private async checkAdmin(userId: number): Promise<boolean> {
    try {
      const result: Record<string, unknown> =
        await this.springClient.isAdminUser(userId);
      return SpringClientService.extractData<boolean>(result) === true;
    } catch (error: unknown) {
      const message: string =
        error instanceof Error ? error.message : String(error);
      this.logger.error(Messages.ADMIN_PERMISSION_CHECK_FAILED(message));
      throw BusinessException.internalServerError(
        Messages.ADMIN_PERMISSION_CHECK_FAILED(message),
        ErrorIds.ADMIN_PERMISSION_CHECK_FAILED,
      );
    }
  }
}
