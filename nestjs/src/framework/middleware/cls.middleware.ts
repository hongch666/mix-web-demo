import { Injectable, NestMiddleware } from '@nestjs/common';
import type { FastifyReply, FastifyRequest } from 'fastify';
import { ClsService } from 'nestjs-cls';

@Injectable()
export class ClsMiddleware implements NestMiddleware {
  constructor(private readonly cls: ClsService) {}

  use(req: FastifyRequest, _res: FastifyReply, next: () => void): void {
    // Fastify 会将所有头部转换为小写，这里统一把 userId 规整成 number 再写入 CLS
    const rawUserId: string | string[] | undefined = req.headers['x-user-id'];
    const rawUsername: string | string[] | undefined =
      req.headers['x-username'];
    const userId: number | undefined = this.parseUserId(rawUserId);
    const username: string = this.parseUsername(rawUsername);

    this.cls.set('userId', userId);
    this.cls.set('username', username);
    next();
  }

  private parseUserId(value: string | string[] | undefined): number | undefined {
    if (Array.isArray(value)) {
      return this.parseUserId(value[0]);
    }

    if (!value) {
      return undefined;
    }

    const userId: number = Number(value);
    return Number.isInteger(userId) && userId > 0 ? userId : undefined;
  }

  private parseUsername(value: string | string[] | undefined): string {
    if (Array.isArray(value)) {
      return value[0] || '';
    }

    return value || '';
  }
}
