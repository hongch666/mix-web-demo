import { Injectable, NestMiddleware } from '@nestjs/common';
import { FastifyRequest, FastifyReply } from 'fastify';
import { ClsService } from 'nestjs-cls';

@Injectable()
export class ClsMiddleware implements NestMiddleware {
  constructor(private readonly cls: ClsService) {}

  use(req: FastifyRequest, res: FastifyReply, next: () => void) {
    // userId 在请求头中，这里使用 X-User-Id
    const userId = req.headers['X-User-Id'];
    const username = req.headers['X-Username'];
    this.cls.set('userId', userId);
    this.cls.set('username', username);
    next();
  }
}
