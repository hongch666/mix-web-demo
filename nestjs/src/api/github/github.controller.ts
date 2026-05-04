import { Controller, Get, Query, Res } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import type { FastifyReply } from 'fastify';
import { HttpCode } from 'src/common/utils/httpCode';
import { ApiResponse, success } from 'src/common/utils/response';
import { ApiLog } from 'src/framework/decorators/apiLog.decorator';
import {
  GithubAuthorizeQueryDto,
  GithubCallbackQueryDto,
} from './dto/github.dto';
import { GithubService } from './github.service';

@Controller('github')
@ApiTags('GitHub 登录模块')
export class GithubController {
  constructor(private readonly githubService: GithubService) {}

  @Get('authorize')
  @ApiOperation({
    summary: '获取 GitHub 授权地址',
    description: '返回 GitHub OAuth 授权地址，前端拿到后直接跳转',
  })
  @ApiLog('获取 GitHub 授权地址')
  async authorize(
    @Query() query: GithubAuthorizeQueryDto,
  ): Promise<ApiResponse<{ authorizeUrl: string; state: string }>> {
    const data = await this.githubService.buildAuthorizeUrl(query);
    return success(data);
  }

  @Get('callback')
  @ApiOperation({
    summary: 'GitHub 回调处理',
    description: '处理 GitHub OAuth 回调，成功后重定向到前端成功页',
  })
  @ApiLog('GitHub 回调处理')
  async callback(
    @Query() query: GithubCallbackQueryDto,
    @Res() reply: FastifyReply,
  ): Promise<void> {
    const redirectUrl = await this.githubService.handleCallback(query);
    reply.code(HttpCode.FOUND).header('Location', redirectUrl).send();
  }
}
