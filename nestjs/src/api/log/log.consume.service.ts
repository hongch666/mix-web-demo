import { Injectable, OnModuleInit } from '@nestjs/common';
import { RabbitMQService } from 'src/modules/mq/mq.service';
import { ArticleLogService } from './log.service';
import { fileLogger } from 'src/common/utils/writeLog';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';

@Injectable()
export class LogConsumerService implements OnModuleInit {
  constructor(
    private readonly rabbitMQService: RabbitMQService,
    private readonly articleLogService: ArticleLogService,
  ) {}

  async onModuleInit() {
    fileLogger.info(Constants.ARTICLE_RABBITMQ_START);
    await this.rabbitMQService.consume('log-queue', async (msg) => {
      try {
        // 处理两种消息格式：
        // 1. 对象
        // 2. JSON 字符串
        let logData = msg;

        if (typeof msg === 'string') {
          // 如果是字符串，尝试解析为 JSON
          logData = JSON.parse(msg);
          fileLogger.info(`接收到 Spring 发送的 ArticleLog 消息: ${msg}`);
        } else {
          // 如果已是对象，直接使用
          fileLogger.info(`接收到 ArticleLog 消息: ${JSON.stringify(logData)}`);
        }

        // 处理消息
        await this.handleMessage(logData);

        fileLogger.info(Constants.ARTICLE_HANDLER);
      } catch (error) {
        fileLogger.error(`处理 ArticleLog 消息失败: ${error.message}`);
      }
    });
  }

  private async handleMessage(msg: any) {
    // 验证必填字段
    if (!msg.action) {
      fileLogger.error(
        `ArticleLog 消息缺少 action 字段: ${JSON.stringify(msg)}`,
      );
      throw new BusinessException(Constants.ARTICLE_LESS_ACTION);
    }

    if (!msg.content) {
      fileLogger.error(
        `ArticleLog 消息缺少 content 字段: ${JSON.stringify(msg)}`,
      );
      throw new BusinessException(Constants.ARTICLE_LESS_CONTNET);
    }

    const dto = {
      articleId: msg.article_id ? msg.article_id : -1,
      userId: msg.user_id ? msg.user_id : -1,
      action: msg.action,
      msg: msg.msg ? msg.msg : null,
      content: msg.content,
    };

    fileLogger.info(`准备保存 ArticleLog: ${JSON.stringify(dto)}`);
    await this.articleLogService.create(dto);
    fileLogger.info(Constants.ARTICLE_SAVE);
  }
}
