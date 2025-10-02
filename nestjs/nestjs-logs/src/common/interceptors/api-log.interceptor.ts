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

@Injectable()
export class ApiLogInterceptor implements NestInterceptor {
  constructor(
    private readonly reflector: Reflector,
    private readonly cls: ClsService,
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
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');

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
        // 计算耗时并记录，保证在响应完成或错误时都会执行
        const durationMs = Date.now() - start;
        const timeMessage = `${method} ${url} 使用了${durationMs}ms`;
        const timeLogMethod = fileLogger[logConfig.logLevel || 'info'];
        if (timeLogMethod) {
          timeLogMethod(timeMessage);
        }
      }),
    );
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
