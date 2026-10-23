import { RabbitSubscribe } from "@golevelup/nestjs-rabbitmq";
import { Injectable, OnApplicationShutdown } from "@nestjs/common";
import { Interval } from "@nestjs/schedule";
import { trace } from "@opentelemetry/api";
import { Defaults, Messages } from "src/common/constants";
import { BatchBuffer } from "src/common/utils/batchBuffer";
import { LoggerService } from "src/module/common/logger/logger.service";
import { ArticleLogService } from "./articleLog.service";
import {
  ArticleAction,
  ArticleLogMessage,
  CreateArticleLogDto,
} from "./dto/articleLog.dto";

type RawArticleLogMessage = Partial<ArticleLogMessage> & {
  user_id?: number;
  article_id?: number;
};

/**
 * 消费 RabbitMQ 的文章日志消息并攒批写入 MongoDB
 */
@Injectable()
export class LogConsumerService implements OnApplicationShutdown {
  private readonly batchBuffer: BatchBuffer<CreateArticleLogDto>;

  constructor(
    private readonly articleLogService: ArticleLogService,
    private readonly logger: LoggerService,
  ) {
    this.batchBuffer = new BatchBuffer<CreateArticleLogDto>(
      "ArticleLog",
      {
        batchSize: Defaults.LOG_BATCH_SIZE,
        flushIntervalMs: Defaults.LOG_BATCH_FLUSH_INTERVAL_MS,
        maxBufferSize: Defaults.LOG_BATCH_MAX_BUFFER_SIZE,
      },
      async (batch) => {
        await this.articleLogService.insertMany(batch);
      },
      logger,
    );
  }

  /**
   * 定时 flush 攒批缓冲：按 flushIntervalMs 周期触发，保证低并发下数据也能及时落库
   * buffer 为空时 flush() 会快速返回，无副作用
   */
  @Interval(Defaults.LOG_BATCH_FLUSH_INTERVAL_MS)
  async flushPendingLogs(): Promise<void> {
    // 定时 flush 没有请求入口，手动开启一段根 span，让批次日志关联到本次执行
    await trace
      .getTracer(Defaults.OTEL_TRACER_NAME)
      .startActiveSpan("job:article-log-flush", async (span) => {
        try {
          await this.batchBuffer.flush();
        } catch (error: unknown) {
          span.recordException(error as Error);
          throw error;
        } finally {
          span.end();
        }
      });
  }

  /**
   * 应用关闭时停止攒批缓冲并将剩余日志落库
   */
  async onApplicationShutdown(): Promise<void> {
    await this.batchBuffer.shutdown();
  }

  /**
   * 订阅 article-log-queue 消息，校验必填字段与操作类型后构建 DTO 入攒批队列
   */
  @RabbitSubscribe({
    queue: "article-log-queue",
  })
  async handleArticleLog(msg: unknown): Promise<void> {
    // MQ 消费没有请求上下文，手动开启一段根 span，让消费日志关联到本次处理
    await trace
      .getTracer(Defaults.OTEL_TRACER_NAME)
      .startActiveSpan("mq:article-log-consume", async (span) => {
        try {
          await this.processArticleLog(msg);
        } finally {
          span.end();
        }
      });
  }

  /**
   * 处理单条文章日志消息：字段校验与操作类型判断后入攒批队列
   */
  private async processArticleLog(msg: unknown): Promise<void> {
    try {
      // 处理两种消息格式：1.对象, 2.JSON 字符串
      let logData: RawArticleLogMessage;

      if (typeof msg === "string") {
        logData = JSON.parse(msg) as RawArticleLogMessage;
      } else {
        logData = msg as RawArticleLogMessage;
      }

      const dto = this.buildDto({
        action: logData.action!,
        content: logData.content!,
        msg: logData.msg,
        userId: logData.userId ?? logData.user_id ?? -1,
        articleId: logData.articleId ?? logData.article_id ?? -1,
      });

      if (dto) {
        this.batchBuffer.enqueue(dto);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      this.logger.error(Messages.ARTICLE_LOG_PROCESS_FAILED(errorMessage));
    }
  }

  /**
   * 校验消息并构建 DTO，无效消息返回 null
   */
  private buildDto(msg: ArticleLogMessage): CreateArticleLogDto | null {
    // 验证必填字段
    if (!msg.action) {
      this.logger.error(
        Messages.ARTICLE_LOG_MISSING_ACTION(JSON.stringify(msg)),
      );
      return null;
    }

    if (!msg.content) {
      this.logger.error(
        Messages.ARTICLE_LOG_MISSING_CONTENT(JSON.stringify(msg)),
      );
      return null;
    }

    // 验证 action 是否是有效的枚举值
    const validActions: ArticleAction[] = Object.values(ArticleAction);
    if (!validActions.includes(msg.action)) {
      this.logger.error(Messages.ARTICLE_LOG_INVALID_ACTION_DETAIL(msg.action));
      return null;
    }

    // 解析 content 为对象（如果是 JSON 字符串）
    let contentObj: Record<string, unknown>;
    if (typeof msg.content === "string") {
      try {
        contentObj = JSON.parse(msg.content) as Record<string, unknown>;
      } catch {
        contentObj = { value: msg.content };
      }
    } else {
      contentObj = msg.content;
    }

    return {
      articleId: msg.articleId ? msg.articleId : -1,
      userId: msg.userId ? msg.userId : -1,
      action: msg.action,
      msg: msg.msg ? msg.msg : undefined,
      content: contentObj,
    };
  }
}
