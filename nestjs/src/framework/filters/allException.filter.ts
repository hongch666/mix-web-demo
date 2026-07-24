import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
} from "@nestjs/common";
import type { FastifyReply, FastifyRequest } from "fastify";
import { ErrorIds, HttpCode, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { error } from "src/common/utils/response";
import { logger } from "src/common/utils/writeLog";

interface HttpExceptionResponse {
  message?: string | string[];
}

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response: FastifyReply = ctx.getResponse<FastifyReply>();
    const request: FastifyRequest = ctx.getRequest<FastifyRequest>();

    let message: string = Messages.ERROR_DEFAULT_MSG;
    let httpStatus: number = HttpCode.INTERNAL_SERVER_ERROR;
    let errorIdentifier: string = ErrorIds.NESTJS_SERVER_ERROR;

    if (exception instanceof BusinessException) {
      // 业务异常：使用其状态码和消息，暴露给客户端
      const res: string | object = exception.getResponse();
      if (typeof res === "string") {
        message = res;
      } else {
        const exceptionResponse = res as HttpExceptionResponse;
        if (typeof exceptionResponse.message === "string") {
          message = exceptionResponse.message;
        } else if (Array.isArray(exceptionResponse.message)) {
          message = exceptionResponse.message.join("; ");
        }
      }
      httpStatus = exception.getStatus();
      errorIdentifier = exception.getErrorIdentifier();
    } else if (exception instanceof HttpException) {
      // 其他 HttpException 只返回通用错误信息
      message = Messages.ERROR_DEFAULT_MSG;
      httpStatus = exception.getStatus();
      errorIdentifier = ErrorIds.NESTJS_SERVER_ERROR;
    } else if (typeof exception === "string") {
      // 其他字符串异常也只返回通用错误信息
      message = Messages.ERROR_DEFAULT_MSG;
      httpStatus = HttpCode.INTERNAL_SERVER_ERROR;
      errorIdentifier = ErrorIds.NESTJS_SERVER_ERROR;
    }

    const exceptionMessage =
      exception instanceof Error
        ? exception.message
        : Messages.ERROR_DEFAULT_MSG;
    const exceptionStack = exception instanceof Error ? exception.stack : "";

    // 打印错误日志（所有异常都记录详细信息）
    logger.error(
      Messages.EXCEPTION_LOG(
        request.method,
        request.url,
        errorIdentifier,
        exception instanceof BusinessException ? message : exceptionMessage,
        exceptionStack,
      ),
    );

    response.status(httpStatus).send(error(httpStatus, message));
  }
}
