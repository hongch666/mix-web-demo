import { SetMetadata, applyDecorators } from "@nestjs/common";

export const REQUIRE_SELF_KEY = "require_self";
export const REQUIRE_SELF_OPTIONS_KEY = "require_self_options";

/**
 * 目标用户标识的来源，query 取查询参数、param 取路径参数、body 取请求体字段
 */
export type RequireSelfSource = "query" | "param" | "body";

/**
 * 本人或管理员校验的配置项
 */
export interface RequireSelfOptions {
  /**
   * 目标用户标识来源，默认查询参数
   */
  source?: RequireSelfSource;

  /**
   * 目标用户标识的参数名，默认 user_id
   */
  paramName?: string;
}

/**
 * 限制用户只能访问本人数据、管理员可访问其他用户数据的装饰器
 * 校验由全局 RequireSelfGuard 执行，控制器按业务参数取值，未传目标用户时使用 CLS 中的当前登录用户
 * @example
 * @RequireSelf()
 * @Get("")
 * async getAllSettings(@Query() query: TableSettingsQueryDto) {
 *   const userId: number = query.user_id ?? this.cls.get<number>("userId");
 * }
 *
 * @RequireSelf({ source: "param", paramName: "user_id" })
 * @Get(":user_id")
 * async getUserDetail(@Param("user_id") userId: number) {}
 */
export const RequireSelf = (
  options: RequireSelfOptions = {},
): MethodDecorator & ClassDecorator =>
  applyDecorators(
    SetMetadata(REQUIRE_SELF_KEY, true),
    SetMetadata(REQUIRE_SELF_OPTIONS_KEY, options),
  );
