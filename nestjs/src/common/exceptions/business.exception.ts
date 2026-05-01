import { HttpException } from '@nestjs/common';
import { HttpCode } from 'src/common/utils/httpCode';

/**
 * 业务异常 - 用于返回可向客户端显示的错误信息
 * 其他未捕获的异常会统一返回 "服务器内部错误"
 */
export class BusinessException extends HttpException {
  /**
   * 错误标识，用于区分同一状态码下的不同错误场景
   */
  readonly error: string;

  constructor(
    message: string,
    status: number = HttpCode.BAD_REQUEST,
    error: string = 'BUSINESS_ERROR',
  ) {
    super(message, status);
    this.error = error;
  }

  /**
   * 获取错误标识
   */
  getErrorIdentifier(): string {
    return this.error;
  }

  // 便捷构造函数

  /**
   * 创建 400 Bad Request 业务异常
   */
  static badRequest(message: string, error: string = 'BAD_REQUEST'): BusinessException {
    return new BusinessException(message, HttpCode.BAD_REQUEST, error);
  }

  /**
   * 创建 401 Unauthorized 业务异常
   */
  static unauthorized(message: string, error: string = 'UNAUTHORIZED'): BusinessException {
    return new BusinessException(message, HttpCode.UNAUTHORIZED, error);
  }

  /**
   * 创建 403 Forbidden 业务异常
   */
  static forbidden(message: string, error: string = 'FORBIDDEN'): BusinessException {
    return new BusinessException(message, HttpCode.FORBIDDEN, error);
  }

  /**
   * 创建 404 Not Found 业务异常
   */
  static notFound(message: string, error: string = 'NOT_FOUND'): BusinessException {
    return new BusinessException(message, HttpCode.NOT_FOUND, error);
  }

  /**
   * 创建 409 Conflict 业务异常
   */
  static conflict(message: string, error: string = 'CONFLICT'): BusinessException {
    return new BusinessException(message, HttpCode.CONFLICT, error);
  }

  /**
   * 创建 422 Unprocessable Entity 业务异常
   */
  static unprocessableEntity(message: string, error: string = 'UNPROCESSABLE_ENTITY'): BusinessException {
    return new BusinessException(message, HttpCode.UNPROCESSABLE_ENTITY, error);
  }

  /**
   * 创建 500 Internal Server Error 业务异常
   */
  static internalServerError(message: string, error: string = 'INTERNAL_SERVER_ERROR'): BusinessException {
    return new BusinessException(message, HttpCode.INTERNAL_SERVER_ERROR, error);
  }

  /**
   * 创建 502 Bad Gateway 业务异常
   */
  static badGateway(message: string, error: string = 'BAD_GATEWAY'): BusinessException {
    return new BusinessException(message, HttpCode.BAD_GATEWAY, error);
  }

  /**
   * 创建 503 Service Unavailable 业务异常
   */
  static serviceUnavailable(message: string, error: string = 'SERVICE_UNAVAILABLE'): BusinessException {
    return new BusinessException(message, HttpCode.SERVICE_UNAVAILABLE, error);
  }

  /**
   * 创建 504 Gateway Timeout 业务异常
   */
  static gatewayTimeout(message: string, error: string = 'GATEWAY_TIMEOUT'): BusinessException {
    return new BusinessException(message, HttpCode.GATEWAY_TIMEOUT, error);
  }
}
