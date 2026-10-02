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

@Injectable()
export class MetricsInterceptor implements NestInterceptor {
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

  private record(method: string, route: string, status: string): void {
    httpRequests.labels(method, route, status).inc();
  }
}
