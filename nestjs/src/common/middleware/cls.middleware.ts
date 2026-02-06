import { Injectable, NestMiddleware } from '@nestjs/common';
import { FastifyRequest, FastifyReply } from 'fastify';
import { ClsService } from 'nestjs-cls';

@Injectable()
export class ClsMiddleware implements NestMiddleware {
  constructor(private readonly cls: ClsService) {}

  use(req: FastifyRequest, res: FastifyReply, next: () => void): void {
    // userId 在请求头中，这里使用 x-user-id（小写），由于 Fastify 会将所有头部转换为小写
    const userId: string | string[] | undefined = req.headers['x-user-id'];
    const username: string | string[] | undefined = req.headers['x-username'];
    this.cls.set('userId', userId);
    this.cls.set('username', username);
    next();
  }
}
