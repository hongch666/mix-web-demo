import { RabbitSubscribe } from "@golevelup/nestjs-rabbitmq";
import { Injectable, OnApplicationShutdown } from "@nestjs/common";
import { Interval } from "@nestjs/schedule";
import { Defaults, Messages } from "src/common/constants";
import { BatchBuffer } from "src/common/utils/batchBuffer";
import { logger } from "src/common/utils/writeLog";
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

@Injectable()
export class LogConsumerService implements OnApplicationShutdown {
  private readonly batchBuffer: BatchBuffer<CreateArticleLogDto>;

  constructor(private readonly articleLogService: ArticleLogService) {
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
    );
  }

  /**
   * 定时 flush 攒批缓冲：按 flushIntervalMs 周期触发，保证低并发下数据也能及时落库。
   * buffer 为空时 flush() 会快速返回，无副作用。
   */
  @Interval(Defaults.LOG_BATCH_FLUSH_INTERVAL_MS)
  async flushPendingLogs(): Promise<void> {
    await this.batchBuffer.flush();
  }

  async onApplicationShutdown(): Promise<void> {
    await this.batchBuffer.shutdown();
  }

  @RabbitSubscribe({
    queue: "article-log-queue",
  })
  async handleArticleLog(msg: unknown): Promise<void> {
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
      logger.error(Messages.ARTICLE_LOG_PROCESS_FAILED(errorMessage));
    }
  }

  /**
   * 校验消息并构建 DTO，无效消息返回 null
   */
  private buildDto(msg: ArticleLogMessage): CreateArticleLogDto | null {
    // 验证必填字段
    if (!msg.action) {
      logger.error(Messages.ARTICLE_LOG_MISSING_ACTION(JSON.stringify(msg)));
      return null;
    }

    if (!msg.content) {
      logger.error(Messages.ARTICLE_LOG_MISSING_CONTENT(JSON.stringify(msg)));
      return null;
    }

    // 验证 action 是否是有效的枚举值
    const validActions: ArticleAction[] = Object.values(ArticleAction);
    if (!validActions.includes(msg.action)) {
      logger.error(Messages.ARTICLE_LOG_INVALID_ACTION_DETAIL(msg.action));
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
