import { RabbitSubscribe } from "@golevelup/nestjs-rabbitmq";
import { Injectable } from "@nestjs/common";
import { Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
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
export class LogConsumerService {
  constructor(private readonly articleLogService: ArticleLogService) {}

  @RabbitSubscribe({
    queue: "article-log-queue",
  })
  async handleArticleLog(msg: unknown): Promise<void> {
    try {
      logger.info(Messages.ARTICLE_RABBITMQ_START);

      // 处理两种消息格式：1.对象, 2.JSON 字符串
      let logData: RawArticleLogMessage;

      if (typeof msg === "string") {
        // 如果是字符串，尝试解析为 JSON
        logData = JSON.parse(msg) as RawArticleLogMessage;
        logger.info(Messages.ARTICLE_LOG_SPRING_MESSAGE(String(msg)));
      } else {
        // 如果已是对象，直接使用
        logData = msg as RawArticleLogMessage;
        logger.info(Messages.ARTICLE_LOG_MESSAGE(JSON.stringify(logData)));
      }

      // 处理消息
      await this.handleMessage({
        action: logData.action!,
        content: logData.content!,
        msg: logData.msg,
        userId: logData.userId ?? logData.user_id ?? -1,
        articleId: logData.articleId ?? logData.article_id ?? -1,
      });

      logger.info(Messages.ARTICLE_HANDLER);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      logger.error(Messages.ARTICLE_LOG_PROCESS_FAILED(errorMessage));
    }
  }

  private async handleMessage(msg: ArticleLogMessage): Promise<void> {
    // 验证必填字段
    if (!msg.action) {
      logger.error(Messages.ARTICLE_LOG_MISSING_ACTION(JSON.stringify(msg)));
      throw BusinessException.unprocessableEntity(Messages.ARTICLE_LESS_ACTION);
    }

    if (!msg.content) {
      logger.error(Messages.ARTICLE_LOG_MISSING_CONTENT(JSON.stringify(msg)));
      throw BusinessException.unprocessableEntity(
        Messages.ARTICLE_LESS_CONTNET,
      );
    }

    // 验证 action 是否是有效的枚举值
    const validActions: ArticleAction[] = Object.values(ArticleAction);
    if (!validActions.includes(msg.action)) {
      logger.error(Messages.ARTICLE_LOG_INVALID_ACTION_DETAIL(msg.action));
      throw BusinessException.unprocessableEntity(
        Messages.ARTICLE_LOG_INVALID_ACTION(msg.action),
      );
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

    const dto: CreateArticleLogDto = {
      articleId: msg.articleId ? msg.articleId : -1,
      userId: msg.userId ? msg.userId : -1,
      action: msg.action,
      msg: msg.msg ? msg.msg : undefined,
      content: contentObj,
    };

    logger.info(Messages.ARTICLE_LOG_PREPARE_SAVE(JSON.stringify(dto)));
    await this.articleLogService.create(dto);
    logger.info(Messages.ARTICLE_SAVE);
  }
}
