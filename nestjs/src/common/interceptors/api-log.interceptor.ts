import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ClsService } from 'nestjs-cls';
import { Observable } from 'rxjs';
import { finalize } from 'rxjs/operators';
import { logger } from '../utils/writeLog';
import { API_LOG_KEY, ApiLogOptions } from '../decorators/api-log.decorator';
import { RabbitMQService } from '../../modules/mq/mq.service';
import { Constants } from '../utils/constants';

@Injectable()
export class ApiLogInterceptor implements NestInterceptor {
  constructor(
    private readonly reflector: Reflector,
    private readonly cls: ClsService,
    private readonly rabbitMQService: RabbitMQService,
  ) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    // 获取装饰器配置
    const logConfig: ApiLogOptions | undefined = this.reflector.get<ApiLogOptions>(
      API_LOG_KEY,
      context.getHandler(),
    );

    if (!logConfig) {
      return next.handle();
    }

    const request: Record<string, unknown> = context.switchToHttp().getRequest();
    const method: string = (request.method as string) || 'UNKNOWN';
    const url: string = (() => {
      if (request.route && typeof request.route === 'object' && 'path' in request.route) {
        const path = (request.route as Record<string, unknown>).path;
        if (typeof path === 'string' && path) {
          return path;
        }
      }
      if (typeof request.url === 'string') {
        const splitUrl = request.url.split('?')[0];
        return splitUrl || 'UNKNOWN';
      }
      return 'UNKNOWN';
    })();

    // 获取用户信息
    const userId: number = this.cls.get<number>('userId') || 0;
    const username: string = this.cls.get<string>('username') || 'unknown';

    // 构建基础日志消息
    let logMessage: string = `用户${userId}:${username} ${method} ${url}: ${logConfig.message}`;

    // 添加参数信息
    if (logConfig.includeParams) {
      const params: string = this.extractParams(context, logConfig.excludeFields);
      if (params) {
        logMessage += `\n${params}`;
      }
    }

    // 记录日志
    const logLevel: string = logConfig.logLevel || 'info';
    if (logLevel in logger) {
      (logger[logLevel as keyof typeof logger] as (message: string) => void)(logMessage);
    }

    // 开始计时
    const start: number = Date.now();

    return next.handle().pipe(
      finalize(() => {
        // 计算耗时
        const responseTime: number = Date.now() - start;
        const timeMessage: string = `${method} ${url} 使用了${responseTime}ms`;
        const timeLogLevel: string = logConfig.logLevel || 'info';
        if (timeLogLevel in logger) {
          (logger[timeLogLevel as keyof typeof logger] as (message: string) => void)(timeMessage);
        }

        // 向消息队列发送 API 日志
        this.sendApiLogToQueue(
          request,
          userId,
          username,
          logConfig.message,
          method,
          url,
          responseTime,
          logConfig.excludeFields,
        ).catch((error: unknown) => {
          const errorMessage: string = error instanceof Error ? error.message : String(error);
          logger.error(`发送 API 日志到队列失败: ${errorMessage}`);
        });
      }),
    );
  }

  /**
   * 向消息队列发送 API 日志
   */
  private async sendApiLogToQueue(
    request: Record<string, unknown>,
    userId: number,
    username: string,
    description: string,
    method: string,
    path: string,
    responseTime: number,
    excludeFields: string[] = [],
  ): Promise<void> {
    try {
      // 提取查询参数
      const queryParams: Record<string, unknown> | null = method === 'GET' && request.query ? (request.query as Record<string, unknown>) : null;

      // 提取路径参数
      const pathParams: Record<string, unknown> | null =
        request.params && typeof request.params === 'object' && Object.keys(request.params as Record<string, unknown>).length > 0
          ? (request.params as Record<string, unknown>)
          : null;

      // 提取请求体
      let requestBody: Record<string, unknown> | null = null;
      if (method !== 'GET' && request.body && typeof request.body === 'object') {
        requestBody = this.filterFields(request.body as Record<string, unknown>, excludeFields);
      }

      // 构建消息对象
      const apiLogMessage: Record<string, unknown> = {
        user_id: userId,
        username: username,
        api_description: description,
        api_path: path,
        api_method: method,
        query_params: queryParams,
        path_params: pathParams,
        request_body: requestBody,
        response_time: responseTime,
      };

      // 发送到消息队列
      await this.rabbitMQService.sendToQueue('api-log-queue', apiLogMessage);

      logger.info(`API 日志已发送到队列: ${JSON.stringify(apiLogMessage)}`);
    } catch (error: unknown) {
      const errorMessage: string = error instanceof Error ? error.message : String(error);
      logger.error(`向消息队列发送 API 日志出错: ${errorMessage}`);
      // 不要抛出异常，避免影响业务逻辑
    }
  }

  private extractParams(
    context: ExecutionContext,
    excludeFields: string[] = [],
  ): string {
    const request: Record<string, unknown> = context.switchToHttp().getRequest();
    const method: string = typeof request.method === 'string' ? request.method : 'UNKNOWN';
    const params: string[] = [];

    try {
      // 处理不同类型的参数
      if (method === 'GET') {
        // Query 参数
        if (request.query && typeof request.query === 'object' && Object.keys(request.query as Record<string, unknown>).length > 0) {
          const filteredQuery: Record<string, unknown> = this.filterFields(request.query as Record<string, unknown>, excludeFields);
          const paramName: string = this.getQueryParamName(context);
          params.push(`${paramName}: ${JSON.stringify(filteredQuery)}`);
        }
      } else {
        // Body 参数
        if (request.body && typeof request.body === 'object' && Object.keys(request.body as Record<string, unknown>).length > 0) {
          const filteredBody: Record<string, unknown> = this.filterFields(request.body as Record<string, unknown>, excludeFields);
          const paramName: string = this.getBodyParamName(context);
          params.push(`${paramName}: ${JSON.stringify(filteredBody)}`);
        }
      }

      // Path 参数
      if (request.params && typeof request.params === 'object' && Object.keys(request.params as Record<string, unknown>).length > 0) {
        const pathParamName: string = this.getPathParamName(context);
        params.push(`${pathParamName}: ${JSON.stringify(request.params)}`);
      }

      return params.join('\n');
    } catch (error: unknown) {
      return Constants.PARAM_ERROR;
    }
  }

  private getQueryParamName(context: ExecutionContext): string {
    // 对于GET请求的查询参数，通常使用DTO名称
    const handler = context.getHandler();
    const handlerName = handler.name;

    // 根据方法名推断参数类型
    if (
      handlerName.includes('find') ||
      handlerName.includes('query') ||
      handlerName.includes('search')
    ) {
      return 'QueryDto';
    }
    return 'Query参数';
  }

  private getBodyParamName(context: ExecutionContext): string {
    // 对于POST/PUT请求的body参数，通常使用DTO名称
    const handler = context.getHandler();
    const handlerName = handler.name;

    // 根据方法名推断参数类型
    if (handlerName.includes('create')) {
      return 'CreateDto';
    } else if (handlerName.includes('update')) {
      return 'UpdateDto';
    }
    return 'RequestBody';
  }

  private getPathParamName(context: ExecutionContext): string {
    const request: Record<string, unknown> = context.switchToHttp().getRequest();
    const paramKeys: string[] = request.params && typeof request.params === 'object' ? Object.keys(request.params as Record<string, unknown>) : [];

    if (paramKeys.length === 1) {
      const paramKey = paramKeys[0];
      if (paramKey) {
        return paramKey.toUpperCase();
      }
    }
    if (paramKeys.length > 1) {
      return 'PARAMS';
    }
    return 'PathParams';
  }

  private filterFields(obj: Record<string, unknown>, excludeFields: string[]): Record<string, unknown> {
    if (!excludeFields || !excludeFields.length) return obj;

    const filtered: Record<string, unknown> = { ...obj };
    excludeFields.forEach((field: string) => {
      delete filtered[field];
    });
    return filtered;
  }
}
