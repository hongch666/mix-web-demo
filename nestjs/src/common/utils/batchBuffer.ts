import { Messages } from "src/common/constants";
import { logger } from "src/common/utils/writeLog";

/**
 * 攒批配置选项
 */
export interface BatchBufferOptions {
  /** 批量大小：达到此数量立即 flush */
  batchSize: number;
  /** flush 间隔（毫秒）：由外部定时任务按此间隔触发 flush */
  flushIntervalMs: number;
  /** 缓冲区最大容量：超过后强制 flush 防止 OOM */
  maxBufferSize: number;
}

const DEFAULT_OPTIONS: BatchBufferOptions = {
  batchSize: 100,
  flushIntervalMs: 2000,
  maxBufferSize: 5000,
};

/**
 * 通用攒批缓冲区
 *
 * 触发 flush 条件（满足其一）：
 * 1. 缓冲区数量 >= batchSize（enqueue 时立即触发）
 * 2. 距上次 flush 时间 >= flushIntervalMs（由外部定时任务统一触发）
 * 3. 缓冲区数量 >= maxBufferSize（强制 flush 防止 OOM）
 *
 * 说明：本类不内置 setTimeout 定时器，定时 flush 由外部定时任务
 * （如 @nestjs/schedule 的 @Interval）调用 flush() 完成，避免内部定时器
 * 生命周期维护带来的"定时器耗尽后不再重启"问题。
 */
export class BatchBuffer<T> {
  private buffer: T[] = [];
  private isFlushing = false;
  private isShutdown = false;
  private flushCompleteResolver: (() => void) | null = null;
  private flushCompletePromise: Promise<void> | null = null;
  private readonly options: BatchBufferOptions;
  private readonly onFlush: (batch: T[]) => Promise<void>;
  private readonly name: string;

  constructor(
    name: string,
    options: Partial<BatchBufferOptions>,
    onFlush: (batch: T[]) => Promise<void>,
  ) {
    this.name = name;
    this.options = { ...DEFAULT_OPTIONS, ...options };
    this.onFlush = onFlush;
    logger.info(
      Messages.BATCH_INITIALIZED(
        this.name,
        this.options.batchSize,
        this.options.flushIntervalMs,
      ),
    );
  }

  /**
   * 入队一条数据
   */
  enqueue(item: T): void {
    if (this.isShutdown) {
      logger.warning(Messages.BATCH_DISCARDED_AFTER_SHUTDOWN(this.name));
      return;
    }
    this.buffer.push(item);

    // 数量达到阈值，立即 flush
    if (this.buffer.length >= this.options.batchSize) {
      this.scheduleFlush();
      return;
    }

    // 超过最大容量，强制 flush 防止 OOM
    if (this.buffer.length >= this.options.maxBufferSize) {
      logger.warning(
        Messages.BATCH_FORCE_FLUSH_MAX_CAPACITY(
          this.name,
          this.options.maxBufferSize,
        ),
      );
      this.scheduleFlush();
    }
  }

  /**
   * 立即 flush 缓冲区（由外部定时任务按 flushIntervalMs 周期调用）
   */
  async flush(): Promise<void> {
    if (this.isShutdown || this.isFlushing || this.buffer.length === 0) {
      return;
    }
    await this.doFlush();
  }

  /**
   * 优雅关闭：flush 剩余数据
   */
  async shutdown(): Promise<void> {
    this.isShutdown = true;
    // 等待当前正在进行的 flush 完成（使用 Promise 通知，避免轮询）
    if (this.isFlushing) {
      await this.flushCompletePromise;
    }
    // flush 剩余数据（直接调用 doFlush，绕过 flush() 的 isShutdown 检查）
    if (this.buffer.length > 0) {
      logger.info(
        Messages.BATCH_SHUTDOWN_FLUSH_REMAINING(this.name, this.buffer.length),
      );
      await this.doFlush();
    }
    logger.info(Messages.BATCH_SHUTDOWN_COMPLETED(this.name));
  }

  /**
   * 获取当前缓冲区大小（用于监控）
   */
  get size(): number {
    return this.buffer.length;
  }

  // ========== 私有方法 ==========

  /**
   * 执行 flush 核心逻辑（不含前置守卫检查）
   * 由 flush() 和 shutdown() 调用
   */
  private async doFlush(): Promise<void> {
    this.isFlushing = true;
    // 创建 Promise 用于通知 flush 完成
    this.flushCompletePromise = new Promise((resolve) => {
      this.flushCompleteResolver = resolve;
    });

    const batch = this.buffer.splice(0, this.buffer.length);
    const batchSize = batch.length;
    try {
      await this.onFlush(batch);
      logger.info(Messages.BATCH_FLUSH_SUCCESS(this.name, batchSize));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      logger.error(
        Messages.BATCH_FLUSH_FAILED_DETAIL(this.name, batchSize, errorMessage),
      );
    } finally {
      this.isFlushing = false;
      // 通知等待者 flush 已完成
      if (this.flushCompleteResolver) {
        this.flushCompleteResolver();
        this.flushCompleteResolver = null;
      }
    }
  }

  private scheduleFlush(): void {
    // 使用 setImmediate 避免在 enqueue 调用栈中同步 flush
    setImmediate(() => {
      void this.flush();
    });
  }
}
