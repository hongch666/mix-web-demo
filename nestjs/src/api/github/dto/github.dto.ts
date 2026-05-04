import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsOptional, IsString } from 'class-validator';

export class GithubAuthorizeQueryDto {
  @ApiPropertyOptional({
    description: '登录成功后回跳路径',
    example: '/profile',
  })
  @IsOptional()
  @IsString()
  redirect?: string;
}

export class GithubCallbackQueryDto {
  @ApiPropertyOptional({
    description: 'GitHub 授权码',
    example: 'abc123',
  })
  @IsOptional()
  @IsString()
  code?: string;

  @ApiPropertyOptional({
    description: 'GitHub 授权状态',
    example: 'state123',
  })
  @IsOptional()
  @IsString()
  state?: string;

  @ApiPropertyOptional({
    description: 'GitHub 错误码',
    example: 'access_denied',
  })
  @IsOptional()
  @IsString()
  error?: string;

  @ApiPropertyOptional({
    description: 'GitHub 错误描述',
    example: 'The user denied the request',
  })
  @IsOptional()
  @IsString()
  error_description?: string;
}
