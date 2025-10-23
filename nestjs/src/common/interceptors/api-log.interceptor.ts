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
import { fileLogger } from '../utils/writeLog';
import { API_LOG_KEY, ApiLogOptions } from '../decorators/api-log.decorator';
import { RabbitMQService } from '../mq/mq.service';

@Injectable()
export class ApiLogInterceptor implements NestInterceptor {
  constructor(
    private readonly reflector: Reflector,
    private readonly cls: ClsService,
    private readonly rabbitMQService: RabbitMQService,
  ) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    // 获取装饰器配置
    const logConfig = this.reflector.get<ApiLogOptions>(
      API_LOG_KEY,
      context.getHandler(),
    );

    if (!logConfig) {
      return next.handle();
    }

    const request = context.switchToHttp().getRequest();
    const method = request.method;
    const url = request.route?.path || request.url;

    // 获取用户信息
    const userId = this.cls.get('userId') || 0;
    const username = this.cls.get('username') || 'unknown';

    // 构建基础日志消息
    let logMessage = `用户${userId}:${username} ${method} ${url}: ${logConfig.message}`;

    // 添加参数信息
    if (logConfig.includeParams) {
      const params = this.extractParams(context, logConfig.excludeFields);
      if (params) {
        logMessage += `\n${params}`;
      }
    }

    // 记录日志
    const logMethod = fileLogger[logConfig.logLevel || 'info'];
    if (logMethod) {
      logMethod(logMessage);
    }

    // 开始计时
    const start = Date.now();

    return next.handle().pipe(
      finalize(() => {
        // 计算耗时
        const responseTime = Date.now() - start;
        const timeMessage = `${method} ${url} 使用了${responseTime}ms`;
        const timeLogMethod = fileLogger[logConfig.logLevel || 'info'];
        if (timeLogMethod) {
          timeLogMethod(timeMessage);
        }

        // ✨ 向消息队列发送 API 日志
        this.sendApiLogToQueue(
          request,
          userId,
          username,
          logConfig.message,
          method,
          url,
          responseTime,
          logConfig.excludeFields,
        ).catch((error) => {
          fileLogger.error(`发送 API 日志到队列失败: ${error.message}`);
        });
      }),
    );
  }

  /**
   * 向消息队列发送 API 日志
   */
  private async sendApiLogToQueue(
    request: any,
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
      const queryParams = method === 'GET' ? request.query : null;

      // 提取路径参数
      const pathParams =
        request.params && Object.keys(request.params).length > 0
          ? request.params
          : null;

      // 提取请求体
      let requestBody = null;
      if (method !== 'GET' && request.body) {
        requestBody = this.filterFields(request.body, excludeFields);
      }

      // 构建消息对象
      const apiLogMessage = {
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

      fileLogger.info(`API 日志已发送到队列: ${JSON.stringify(apiLogMessage)}`);
    } catch (error) {
      fileLogger.error(`向消息队列发送 API 日志出错: ${error.message}`);
      // 不要抛出异常，避免影响业务逻辑
    }
  }

  private extractParams(
    context: ExecutionContext,
    excludeFields: string[] = [],
  ): string {
    const request = context.switchToHttp().getRequest();
    const method = request.method;
    const params: string[] = [];

    try {
      // 处理不同类型的参数
      if (method === 'GET') {
        // Query 参数
        if (request.query && Object.keys(request.query).length > 0) {
          const filteredQuery = this.filterFields(request.query, excludeFields);
          const paramName = this.getQueryParamName(context);
          params.push(`${paramName}: ${JSON.stringify(filteredQuery)}`);
        }
      } else {
        // Body 参数
        if (request.body && Object.keys(request.body).length > 0) {
          const filteredBody = this.filterFields(request.body, excludeFields);
          const paramName = this.getBodyParamName(context);
          params.push(`${paramName}: ${JSON.stringify(filteredBody)}`);
        }
      }

      // Path 参数
      if (request.params && Object.keys(request.params).length > 0) {
        const pathParamName = this.getPathParamName(context);
        params.push(`${pathParamName}: ${JSON.stringify(request.params)}`);
      }

      return params.join('\n');
    } catch (error) {
      return '参数解析失败';
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
    const request = context.switchToHttp().getRequest();
    const paramKeys = Object.keys(request.params);

    if (paramKeys.length === 1) {
      return paramKeys[0].toUpperCase();
    } else if (paramKeys.length > 1) {
      return 'PARAMS';
    }
    return 'PathParams';
  }

  private filterFields(obj: any, excludeFields: string[]): any {
    if (!excludeFields || !excludeFields.length) return obj;

    const filtered = { ...obj };
    excludeFields.forEach((field) => {
      delete filtered[field];
    });
    return filtered;
  }
}
