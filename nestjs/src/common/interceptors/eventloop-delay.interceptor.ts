import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { performance } from 'perf_hooks';

@Injectable()
export class EventLoopDelayInterceptor implements NestInterceptor {
  private readonly logger = new Logger(EventLoopDelayInterceptor.name);
  private markStart: string = 'eventloop-start';
  private markEnd: string = 'eventloop-end';
  private measureName: string = 'eventloop-delay';

  intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url } = request;

    // 标记请求开始时间
    const markLabel = `${this.markStart}-${Date.now()}-${Math.random()}`;
    const endMarkLabel = `${this.markEnd}-${Date.now()}-${Math.random()}`;
    
    performance.mark(markLabel);

    return next.handle().pipe(
      tap(() => {
        // 标记请求结束时间
        performance.mark(endMarkLabel);

        try {
          // 计算延迟
          performance.measure(this.measureName, markLabel, endMarkLabel);
          const measures = performance.getEntriesByName(this.measureName);
          
          if (measures.length > 0) {
            const lastMeasure = measures[measures.length - 1];
            const delay = lastMeasure.duration;

            this.logger.debug(
              `[${method}] ${url} - EventLoop 延迟: ${delay.toFixed(2)}ms`,
            );

            // 清理性能标记
            performance.clearMarks(markLabel);
            performance.clearMarks(endMarkLabel);
            performance.clearMeasures(this.measureName);
          }
        } catch (error) {
          this.logger.error('计算 EventLoop 延迟失败:', error);
        }
      }),
    );
  }
}
