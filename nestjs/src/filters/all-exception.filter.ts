import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { error } from '../utils/response'; // 你之前写的 error() 方法

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = '服务器内部错误';

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const res = exception.getResponse();
      if (typeof res === 'string') {
        message = res;
      } else if (typeof res === 'object' && (res as any).message) {
        message = (res as any).message;
      }
    } else if (typeof exception === 'string') {
      message = exception;
    } else if (exception?.message) {
      message = exception.message;
    }

    // 打印错误日志
    console.error(`[${request.method}] ${request.url} - ${message}`);

    response.status(status).json(
      error(message),
    );
  }
}
