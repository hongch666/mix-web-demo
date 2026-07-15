import { CanActivate, ExecutionContext, Injectable } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { ClsService } from "nestjs-cls";
import { HttpCode, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { UserService } from "src/module/common/user/user.service";
import { REQUIRE_ADMIN_KEY } from "../decorators/requireAdmin.decorator";

@Injectable()
export class RequireAdminGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly cls: ClsService,
    private readonly userService: UserService,
  ) {}

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
        "UNAUTHORIZED_USER",
      );
    }

    const isAdmin: boolean = await this.userService.isAdminUser(userId);

    if (!isAdmin) {
      throw new BusinessException(
        Messages.NO_ADMIN_USER,
        HttpCode.FORBIDDEN,
        "NO_ADMIN_PERMISSION",
      );
    }

    return true;
  }
}
