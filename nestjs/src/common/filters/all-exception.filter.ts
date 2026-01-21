import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { FastifyRequest, FastifyReply } from 'fastify';
import { error } from '../utils/response'; // 之前写的 error() 方法
import { fileLogger } from '../utils/writeLog';
import { BusinessException } from '../exceptions/business.exception';

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<FastifyReply>();
    const request = ctx.getRequest<FastifyRequest>();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = 'NestJS服务器错误';
    let isBusinessException = false;

    // 判断是否是业务异常（可向客户端显示）
    if (exception instanceof BusinessException) {
      isBusinessException = true;
      status = exception.getStatus();
      const res = exception.getResponse();
      if (typeof res === 'string') {
        message = res;
      } else if (typeof res === 'object' && (res as any).message) {
        message = (res as any).message;
      }
    } else if (exception instanceof HttpException) {
      // 其他 HttpException 只返回通用错误信息
      status = exception.getStatus();
    } else if (typeof exception === 'string') {
      // 其他字符串异常也只返回通用错误信息
      message = '服务器内部错误';
    }

    // 打印错误日志（所有异常都记录详细信息）
    fileLogger.error(
      `[${request.method}] ${request.url} - ${isBusinessException ? message : exception?.message || '未知错误'} - ${exception.stack}`,
    );

    response.status(status).send(error(message));
  }
}
