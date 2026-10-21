import {
  CallHandler,
  ExecutionContext,
  HttpException,
  Injectable,
  NestInterceptor,
} from "@nestjs/common";
import type { FastifyRequest } from "fastify";
import { Observable, finalize, tap } from "rxjs";
import {
  httpDuration,
  httpRequests,
} from "src/module/common/telemetry/metrics";

/**
 * HTTP 监控指标拦截器，在 createApp 中全局注册，采集各路由的请求计数与响应耗时
 */
@Injectable()
export class MetricsInterceptor implements NestInterceptor {
  /**
   * 按请求方法、路由与状态码统计请求次数，并在请求结束时上报以秒为单位的响应耗时
   */
  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const request: FastifyRequest = context.switchToHttp().getRequest();
    const method: string = request.method;
    const route: string = request.routeOptions?.url || "UNKNOWN";
    const startedAt: bigint = process.hrtime.bigint();
    const response = context.switchToHttp().getResponse();

    return next.handle().pipe(
      tap({
        next: () => this.record(method, route, String(response.statusCode)),
        error: (error: unknown) => {
          const status: number =
            error instanceof HttpException ? error.getStatus() : 500;
          this.record(method, route, String(status));
        },
      }),
      finalize(() => {
        const duration: number =
          Number(process.hrtime.bigint() - startedAt) / 1_000_000_000;
        httpDuration.labels(method, route).observe(duration);
      }),
    );
  }

  /**
   * 按方法、路由与状态码递增 HTTP 请求总数计数器
   */
  private record(method: string, route: string, status: string): void {
    httpRequests.labels(method, route, status).inc();
  }
}
