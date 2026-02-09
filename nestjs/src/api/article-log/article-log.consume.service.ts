import { Injectable, OnModuleInit } from '@nestjs/common';
import { RabbitMQService } from 'src/modules/mq/mq.service';
import { ArticleLogService } from './article-log.service';
import { logger } from 'src/common/utils/writeLog';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import {
  ArticleLogMessage,
  ArticleAction,
  CreateArticleLogDto,
} from './dto/article-log.dto';

@Injectable()
export class LogConsumerService implements OnModuleInit {
  constructor(
    private readonly rabbitMQService: RabbitMQService,
    private readonly articleLogService: ArticleLogService,
  ) {}

  async onModuleInit() {
    logger.info(Constants.ARTICLE_RABBITMQ_START);
    await this.rabbitMQService.consume(
      'log-queue',
      async (msg): Promise<void> => {
        try {
          // 处理两种消息格式：1.对象, 2.JSON 字符串
          let logData: ArticleLogMessage;

          if (typeof msg === 'string') {
            // 如果是字符串，尝试解析为 JSON
            logData = JSON.parse(msg) as ArticleLogMessage;
            logger.info(`接收到 Spring 发送的 ArticleLog 消息: ${String(msg)}`);
          } else {
            // 如果已是对象，直接使用
            logData = msg as ArticleLogMessage;
            logger.info(`接收到 ArticleLog 消息: ${JSON.stringify(logData)}`);
          }

          // 处理消息
          await this.handleMessage(logData);

          logger.info(Constants.ARTICLE_HANDLER);
        } catch (error) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);
          logger.error(`处理 ArticleLog 消息失败: ${errorMessage}`);
        }
      },
    );
  }

  private async handleMessage(msg: ArticleLogMessage) {
    // 验证必填字段
    if (!msg.action) {
      logger.error(`ArticleLog 消息缺少 action 字段: ${JSON.stringify(msg)}`);
      throw new BusinessException(Constants.ARTICLE_LESS_ACTION);
    }

    if (!msg.content) {
      logger.error(`ArticleLog 消息缺少 content 字段: ${JSON.stringify(msg)}`);
      throw new BusinessException(Constants.ARTICLE_LESS_CONTNET);
    }

    // 验证 action 是否是有效的枚举值
    const validActions = Object.values(ArticleAction);
    if (!validActions.includes(msg.action as ArticleAction)) {
      logger.error(`ArticleLog 消息包含无效的 action 值: ${msg.action}`);
      throw new BusinessException(`无效的操作类型: ${msg.action}`);
    }

    // 解析 content 为对象（如果是 JSON 字符串）
    let contentObj: Record<string, any>;
    if (typeof msg.content === 'string') {
      try {
        contentObj = JSON.parse(msg.content) as Record<string, any>;
      } catch {
        contentObj = { value: msg.content };
      }
    } else {
      contentObj = msg.content;
    }

    const dto: CreateArticleLogDto = {
      articleId: msg.article_id ? msg.article_id : -1,
      userId: msg.user_id ? msg.user_id : -1,
      action: msg.action as ArticleAction,
      msg: msg.msg ? msg.msg : undefined,
      content: contentObj,
    };

    logger.info(`准备保存 ArticleLog: ${JSON.stringify(dto)}`);
    await this.articleLogService.create(dto);
    logger.info(Constants.ARTICLE_SAVE);
  }
}
