import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  ForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ClsService } from 'nestjs-cls';
import { Observable } from 'rxjs';
import { REQUIRE_ADMIN_KEY } from '../decorators/require-admin.decorator';
import { UserService } from '../../modules/user/user.service';
import { BusinessException } from '../exceptions/business.exception';

@Injectable()
export class RequireAdminInterceptor implements NestInterceptor {
  constructor(
    private readonly reflector: Reflector,
    private readonly cls: ClsService,
    private readonly userService: UserService,
  ) {}

  async intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Promise<Observable<any>> {
    // 获取装饰器标记
    const requireAdmin = this.reflector.get<boolean>(
      REQUIRE_ADMIN_KEY,
      context.getHandler(),
    );

    // 如果没有标记，直接放行
    if (!requireAdmin) {
      return next.handle();
    }

    // 获取当前用户ID
    const userId = this.cls.get('userId');

    // 如果没有用户ID，拒绝访问
    if (!userId) {
      throw new BusinessException('未授权的用户，无法访问');
    }

    // 检查用户是否是管理员
    const isAdmin = await this.userService.isAdminUser(userId);

    // 非管理员拦截
    if (!isAdmin) {
      throw new BusinessException('当前用户没有管理员权限，无法访问此功能');
    }

    return next.handle();
  }
}
