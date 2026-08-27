import { CanActivate, ExecutionContext, Injectable } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { ClsService } from "nestjs-cls";
import { ErrorIds, HttpCode, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { InternalTokenUtil } from "src/common/utils/internalToken.util";
import { LoggerService } from "src/module/common/logger/logger.service";
import {
  REQUIRE_INTERNAL_TOKEN_KEY,
  REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY,
} from "../decorators/requireInternalToken.decorator";

/**
 * 内部服务令牌验证守卫
 * 用于验证带有 @RequireInternalToken 装饰器的接口的内部令牌
 */
@Injectable()
export class InternalTokenGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly cls: ClsService,
    private readonly internalTokenUtil: InternalTokenUtil,
    private readonly logger: LoggerService,
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

    // 从 CLS 上下文中获取已解析的内部令牌（由 ClsMiddleware 预先解析）
    const internalToken: string = this.cls.get<string>("internalToken") || "";

    if (!internalToken) {
      this.logger.error(Messages.INTERNAL_TOKEN_MISSING);
      throw new BusinessException(
        Messages.INTERNAL_TOKEN_MISSING,
        HttpCode.UNAUTHORIZED,
        ErrorIds.INTERNAL_TOKEN_MISSING_ERROR,
      );
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
        this.logger.error(
          Messages.INTERNAL_TOKEN_SERVICE_NAME_MISMATCH(
            requiredServiceName,
            claims.serviceName,
          ),
        );
        throw new BusinessException(
          Messages.SERVICE_NAME_MISMATCH,
          HttpCode.FORBIDDEN,
          ErrorIds.INTERNAL_TOKEN_SERVICE_MISMATCH,
        );
      }

      this.logger.debug(
        Messages.INTERNAL_TOKEN_VERIFICATION_SUCCESS(
          claims.userId,
          claims.serviceName,
        ),
      );
      return true;
    } catch (error: unknown) {
      if (error instanceof BusinessException) {
        throw error;
      }
      const message = error instanceof Error ? error.message : String(error);
      this.logger.error(Messages.INTERNAL_TOKEN_VERIFICATION_FAILED(message));
      throw new BusinessException(
        Messages.INTERNAL_TOKEN_INVALID,
        HttpCode.UNAUTHORIZED,
        ErrorIds.INTERNAL_TOKEN_INVALID_ERROR,
      );
    }
  }
}
