import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
} from '@nestjs/common';
import type { FastifyReply, FastifyRequest } from 'fastify';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import { HttpCode } from 'src/common/utils/httpCode';
import { error } from 'src/common/utils/response';
import { logger } from 'src/common/utils/writeLog';

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response: FastifyReply = ctx.getResponse<FastifyReply>();
    const request: FastifyRequest = ctx.getRequest<FastifyRequest>();

    let message: string = Constants.ERROR_DEFAULT_MSG;
    let httpStatus: number = HttpCode.INTERNAL_SERVER_ERROR;
    let errorIdentifier: string = 'NESTJS_SERVER_ERROR';

    if (exception instanceof BusinessException) {
      // 业务异常：使用其状态码和消息，暴露给客户端
      const res: string | object = exception.getResponse();
      if (typeof res === 'string') {
        message = res;
      } else if (typeof res === 'object' && (res as any).message) {
        message = (res as any).message;
      }
      httpStatus = exception.getStatus();
      errorIdentifier = exception.getErrorIdentifier();
    } else if (exception instanceof HttpException) {
      // 其他 HttpException 只返回通用错误信息
      message = Constants.ERROR_DEFAULT_MSG;
      httpStatus = exception.getStatus();
      errorIdentifier = 'NESTJS_SERVER_ERROR';
    } else if (typeof exception === 'string') {
      // 其他字符串异常也只返回通用错误信息
      message = Constants.ERROR_DEFAULT_MSG;
      httpStatus = HttpCode.INTERNAL_SERVER_ERROR;
      errorIdentifier = 'NESTJS_SERVER_ERROR';
    }

    // 打印错误日志（所有异常都记录详细信息）
    logger.error(
      `[${request.method}] ${request.url} - [${errorIdentifier}] ${exception instanceof BusinessException ? message : exception?.message || Constants.ERROR_DEFAULT_MSG} - ${exception.stack}`,
    );

    response.status(httpStatus).send(error(httpStatus, message, errorIdentifier));
  }
}
