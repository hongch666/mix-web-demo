import { logger } from "src/common/utils/writeLog";

/**
 * 攒批配置选项
 */
export interface BatchBufferOptions {
  /** 批量大小：达到此数量立即 flush */
  batchSize: number;
  /** flush 间隔（毫秒）：超过此时间未 flush 则自动触发 */
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
 * 1. 缓冲区数量 >= batchSize
 * 2. 距上次 flush 时间 >= flushIntervalMs
 * 3. 缓冲区数量 >= maxBufferSize（强制 flush 防止 OOM）
 *
 * 使用方式：
 * ```
 * const buffer = new BatchBuffer<MyDto>({
 *   batchSize: 100,
 *   flushIntervalMs: 1000,
 * }, async (batch) => { await service.insertMany(batch); });
 *
 * buffer.enqueue(dto1);
 * buffer.enqueue(dto2);
 * // ...
 * await buffer.shutdown(); // 优雅关闭时调用
 * ```
 */
export class BatchBuffer<T> {
  private buffer: T[] = [];
  private flushTimer: ReturnType<typeof setTimeout> | null = null;
  private isFlushing = false;
  private isShutdown = false;
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
    this.startTimer();
    logger.info(
      `[攒批] ${this.name} 初始化完成 (batchSize=${this.options.batchSize}, interval=${this.options.flushIntervalMs}ms)`,
    );
  }

  /**
   * 入队一条数据
   */
  enqueue(item: T): void {
    if (this.isShutdown) {
      logger.warning(`[攒批] ${this.name} 已关闭，丢弃数据`);
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
        `[攒批] ${this.name} 缓冲区达到最大容量 ${this.options.maxBufferSize}，强制 flush`,
      );
      this.scheduleFlush();
    }
  }

  /**
   * 立即 flush 缓冲区（由 enqueue 触发或外部调用）
   */
  async flush(): Promise<void> {
    if (this.isFlushing || this.buffer.length === 0) return;

    this.isFlushing = true;
    this.clearTimer();

    const batch = this.buffer.splice(0, this.buffer.length);
    const batchSize = batch.length;

    try {
      await this.onFlush(batch);
      logger.info(`[攒批] ${this.name} flush 成功，批次大小: ${batchSize}`);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      logger.error(
        `[攒批] ${this.name} flush 失败，批次大小: ${batchSize}，错误: ${errorMessage}`,
      );
    } finally {
      this.isFlushing = false;
      // 如果 flush 期间有新数据入队，启动定时器
      if (this.buffer.length > 0) {
        this.startTimer();
      }
    }
  }

  /**
   * 优雅关闭：flush 剩余数据并停止定时器
   */
  async shutdown(): Promise<void> {
    this.isShutdown = true;
    this.clearTimer();
    // 等待当前正在进行的 flush 完成
    while (this.isFlushing) {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    // flush 剩余数据
    if (this.buffer.length > 0) {
      logger.info(
        `[攒批] ${this.name} 优雅关闭，flush 剩余 ${this.buffer.length} 条数据`,
      );
      await this.flush();
    }
    logger.info(`[攒批] ${this.name} 已关闭`);
  }

  /**
   * 获取当前缓冲区大小（用于监控）
   */
  get size(): number {
    return this.buffer.length;
  }

  // ========== 私有方法 ==========

  private scheduleFlush(): void {
    // 使用 setImmediate 避免在 enqueue 调用栈中同步 flush
    setImmediate(() => {
      void this.flush();
    });
  }

  private startTimer(): void {
    if (this.isShutdown || this.flushTimer) return;
    this.flushTimer = setTimeout(() => {
      void this.flush();
    }, this.options.flushIntervalMs);
  }

  private clearTimer(): void {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }
  }
}
