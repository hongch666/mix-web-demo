import { SetMetadata } from '@nestjs/common';

export const REQUIRE_ADMIN_KEY = 'require_admin';

/**
 * 需要管理员权限的装饰器
 * 用于标记需要管理员身份才能访问的接口
 * 如果用户不是管理员，拦截器会抛出Forbidden异常
 * @example
 * @RequireAdmin()
 * async deleteUser(@Param('id') id: number) {
 *   return await this.userService.deleteUser(id);
 * }
 */
export const RequireAdmin = () => SetMetadata(REQUIRE_ADMIN_KEY, true);
