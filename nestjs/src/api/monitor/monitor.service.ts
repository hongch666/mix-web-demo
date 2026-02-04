import { Injectable, Logger } from '@nestjs/common';
import { PerformanceObserver } from 'perf_hooks';

export interface EventLoopMetrics {
  timestamp: number;
  delay: number;
  maxDelay: number;
  avgDelay: number;
  sampleCount: number;
}

@Injectable()
export class MonitorService {
  private readonly logger = new Logger(MonitorService.name);
  private observer: PerformanceObserver | null = null;
  private delayMetrics: number[] = [];
  private maxSamples: number = 100;
  private measureName: string = 'eventloop-delay';

  /**
   * 启动 EventLoop 延迟监测
   */
  startMonitoring(): void {
    try {
      this.observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name === this.measureName) {
            const delay = entry.duration;
            this.recordDelay(delay);

            if (delay > 100) {
              this.logger.warn(
                `EventLoop 延迟过高: ${delay.toFixed(2)}ms`,
              );
            }
          }
        });
      });

      this.observer.observe({ entryTypes: ['measure'] });
      this.logger.log('EventLoop 监测已启动');
    } catch (error) {
      this.logger.error('启动 EventLoop 监测失败:', error);
    }
  }

  /**
   * 停止监测
   */
  stopMonitoring(): void {
    if (this.observer) {
      this.observer.disconnect();
      this.logger.log('EventLoop 监测已停止');
    }
  }

  /**
   * 记录延迟数据
   */
  private recordDelay(delay: number): void {
    this.delayMetrics.push(delay);
    if (this.delayMetrics.length > this.maxSamples) {
      this.delayMetrics.shift();
    }
  }

  /**
   * 获取 EventLoop 延迟指标
   */
  getMetrics(): EventLoopMetrics {
    if (this.delayMetrics.length === 0) {
      return {
        timestamp: Date.now(),
        delay: 0,
        maxDelay: 0,
        avgDelay: 0,
        sampleCount: 0,
      };
    }

    const maxDelay = Math.max(...this.delayMetrics);
    const avgDelay =
      this.delayMetrics.reduce((a, b) => a + b, 0) /
      this.delayMetrics.length;
    const currentDelay =
      this.delayMetrics[this.delayMetrics.length - 1];

    return {
      timestamp: Date.now(),
      delay: currentDelay,
      maxDelay,
      avgDelay: parseFloat(avgDelay.toFixed(2)),
      sampleCount: this.delayMetrics.length,
    };
  }

  /**
   * 清空指标数据
   */
  clearMetrics(): void {
    this.delayMetrics = [];
  }
}
