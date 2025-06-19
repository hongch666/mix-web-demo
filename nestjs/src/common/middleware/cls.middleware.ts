import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { ClsService } from 'nestjs-cls';

@Injectable()
export class ClsMiddleware implements NestMiddleware {
  constructor(private readonly cls: ClsService) {}

  use(req: Request, res: Response, next: NextFunction) {
    // userId 在请求头中，这里使用 X-User-Id
    const userId = req.header('X-User-Id');
    const username = req.header('X-Username');
    this.cls.set('userId', userId);
    this.cls.set('username', username);
    next();
  }
}
