import { ApiPropertyOptional } from "@nestjs/swagger";
import { IsOptional, IsString } from "class-validator";
import { ExposeName } from "src/framework/serializer/snakeCase.serializer";

/**
 * 获取 GitHub 授权地址接口的查询参数，包含登录成功后的前端回跳路径
 */
export class GithubAuthorizeQueryDto {
  @ApiPropertyOptional({
    description: "登录成功后回跳路径",
    example: "/profile",
  })
  @IsOptional()
  @IsString()
  redirect?: string;
}

/**
 * GitHub OAuth 回调接口的查询参数，包含授权码、state 及错误信息
 */
export class GithubCallbackQueryDto {
  @ApiPropertyOptional({
    description: "GitHub 授权码",
    example: "abc123",
  })
  @IsOptional()
  @IsString()
  code?: string;

  @ApiPropertyOptional({
    description: "GitHub 授权状态",
    example: "state123",
  })
  @IsOptional()
  @IsString()
  state?: string;

  @ApiPropertyOptional({
    description: "GitHub 错误码",
    example: "access_denied",
  })
  @IsOptional()
  @IsString()
  error?: string;

  @ApiPropertyOptional({
    description: "GitHub 错误描述",
    example: "The user denied the request",
  })
  @ExposeName()
  @IsOptional()
  @IsString()
  errorDescription?: string;
}
