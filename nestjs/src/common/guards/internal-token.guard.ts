import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import {
  REQUIRE_INTERNAL_TOKEN_KEY,
  REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY,
} from '../decorators/require-internal-token.decorator';
import { InternalTokenUtil } from '../utils/internal-token.util';
import { BusinessException } from '../exceptions/business.exception';
import { Constants } from '../utils/constants';
import { logger } from '../utils/writeLog';

/**
 * 内部服务令牌验证守卫
 * 用于验证带有 @RequireInternalToken 装饰器的接口的内部令牌
 */
@Injectable()
export class InternalTokenGuard implements CanActivate {
  private static readonly INTERNAL_TOKEN_HEADER = 'x-internal-token';
  private static readonly BEARER_PREFIX = 'Bearer ';

  constructor(
    private readonly reflector: Reflector,
    private readonly internalTokenUtil: InternalTokenUtil,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    // 检查方法是否标有 @RequireInternalToken 装饰器
    const requireInternalToken: boolean | undefined =
      this.reflector.get<boolean>(
        REQUIRE_INTERNAL_TOKEN_KEY,
        context.getHandler(),
      );

    if (!requireInternalToken) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const internalToken = this.extractInternalToken(request);

    if (!internalToken) {
      logger.error(Constants.INTERNAL_TOKEN_MISSING);
      throw new BusinessException(Constants.INTERNAL_TOKEN_MISSING);
    }

    try {
      // 验证令牌
      const claims =
        await this.internalTokenUtil.validateInternalToken(internalToken);

      // 检查服务名称（如果指定了）
      const requiredServiceName: string | undefined =
        this.reflector.get<string>(
          REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY,
          context.getHandler(),
        );

      if (requiredServiceName && requiredServiceName !== claims.serviceName) {
        logger.error(
          `${Constants.SERVICE_NAME_MISMATCH}. 期望: ${requiredServiceName}, 获得: ${claims.serviceName}`,
        );
        throw new BusinessException(Constants.SERVICE_NAME_MISMATCH);
      }

      logger.debug(
        `内部令牌验证成功 - 用户ID: ${claims.userId}, 服务: ${claims.serviceName}`,
      );
      return true;
    } catch (error: any) {
      if (error instanceof BusinessException) {
        throw error;
      }
      logger.error(`令牌验证失败: ${error.message}`);
      throw new BusinessException(Constants.INTERNAL_TOKEN_INVALID);
    }
  }

  /**
   * 从请求头中提取内部令牌
   */
  private extractInternalToken(request: Record<string, unknown>): string | null {
    const authHeader: unknown =
      (request.headers as Record<string, unknown>)?.[InternalTokenGuard.INTERNAL_TOKEN_HEADER];
    if (
      authHeader &&
      typeof authHeader === 'string' &&
      authHeader.startsWith(InternalTokenGuard.BEARER_PREFIX)
    ) {
      return authHeader.substring(InternalTokenGuard.BEARER_PREFIX.length);
    }
    return typeof authHeader === 'string' ? authHeader : null;
  }
}
