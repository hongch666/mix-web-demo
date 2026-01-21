import { HttpException, HttpStatus } from '@nestjs/common';

/**
 * 业务异常 - 用于返回可向客户端显示的错误信息
 * 其他未捕获的异常会统一返回 "服务器内部错误"
 */
export class BusinessException extends HttpException {
  constructor(message: string, status: HttpStatus = HttpStatus.BAD_REQUEST) {
    super(message, status);
  }
}
