import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { FastifyRequest, FastifyReply } from 'fastify';
import { error } from '../utils/response'; // 之前写的 error() 方法
import { logger } from '../utils/writeLog';
import { BusinessException } from '../exceptions/business.exception';
import { Constants } from '../utils/constants';

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response: FastifyReply = ctx.getResponse<FastifyReply>();
    const request: FastifyRequest = ctx.getRequest<FastifyRequest>();

    let message: string = Constants.ERROR_DEFAULT_MSG;
    let isBusinessException: boolean = false;

    // 判断是否是业务异常（可向客户端显示）
    if (exception instanceof BusinessException) {
      isBusinessException = true;
      const res: string | object = exception.getResponse();
      if (typeof res === 'string') {
        message = res;
      } else if (typeof res === 'object' && (res as any).message) {
        message = (res as any).message;
      }
    } else if (exception instanceof HttpException) {
      // 其他 HttpException 只返回通用错误信息
      message = Constants.ERROR_DEFAULT_MSG;
    } else if (typeof exception === 'string') {
      // 其他字符串异常也只返回通用错误信息
      message = Constants.ERROR_DEFAULT_MSG;
    }

    // 打印错误日志（所有异常都记录详细信息）
    logger.error(
      `[${request.method}] ${request.url} - ${isBusinessException ? message : exception?.message || Constants.ERROR_DEFAULT_MSG} - ${exception.stack}`,
    );

    response.status(HttpStatus.OK).send(error(message));
  }
}
