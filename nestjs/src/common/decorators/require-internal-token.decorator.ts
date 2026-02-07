import { SetMetadata, UseGuards, applyDecorators } from '@nestjs/common';
import { InternalTokenGuard } from '../guards/internal-token.guard';

export const REQUIRE_INTERNAL_TOKEN_KEY = 'require_internal_token';
export const REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY =
  'require_internal_token_service_name';

/**
 * 需要内部服务令牌验证的装饰器
 * 同时包含令牌验证逻辑和守卫应用，只需要一个注解
 * @param serviceName 可选参数，指定必须来自特定服务的令牌
 * @example
 * @RequireInternalToken()
 * async getSpring() {
 *   return success(Constants.TEST);
 * }
 *
 * @RequireInternalToken('spring')
 * async getSomething() {
 *   return success(data);
 * }
 */
export const RequireInternalToken = (serviceName?: string) => {
  const decorators: any[] = [
    SetMetadata(REQUIRE_INTERNAL_TOKEN_KEY, true),
    UseGuards(InternalTokenGuard),
  ];

  if (serviceName) {
    decorators.unshift(
      SetMetadata(REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY, serviceName),
    );
  }

  return applyDecorators(...decorators);
};
