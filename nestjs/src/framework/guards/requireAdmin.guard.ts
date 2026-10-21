import { CanActivate, ExecutionContext, Injectable } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { ClsService } from "nestjs-cls";
import { ErrorIds, HttpCode, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { SpringClientService } from "src/module/common/client/springClient.service";
import { REQUIRE_ADMIN_KEY } from "../decorators/requireAdmin.decorator";

/**
 * 管理员权限守卫，通过 APP_GUARD 全局注册，对标注 @RequireAdmin 的接口校验当前用户是否具备管理员权限
 */
@Injectable()
export class RequireAdminGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly cls: ClsService,
    private readonly springClient: SpringClientService,
  ) {}

  /**
   * 从 CLS 上下文获取用户 ID 并调用 Spring 服务查询其管理员身份，非管理员或未登录时拒绝访问
   */
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requireAdmin: boolean | undefined = this.reflector.get<boolean>(
      REQUIRE_ADMIN_KEY,
      context.getHandler(),
    );

    if (!requireAdmin) {
      return true;
    }

    const userId: number | undefined = this.cls.get<number>("userId");

    if (!userId) {
      throw new BusinessException(
        Messages.UNAUTHORIZED_USER,
        HttpCode.FORBIDDEN,
        ErrorIds.UNAUTHORIZED_USER_ERROR,
      );
    }

    const result: Record<string, unknown> =
      await this.springClient.isAdminUser(userId);
    const isAdmin: boolean = SpringClientService.extractData<boolean>(result);

    if (!isAdmin) {
      throw new BusinessException(
        Messages.NO_ADMIN_USER,
        HttpCode.FORBIDDEN,
        ErrorIds.NO_ADMIN_PERMISSION,
      );
    }

    return true;
  }
}
