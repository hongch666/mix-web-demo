import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { RabbitMQService } from 'src/common/mq/mq.service';
import { ArticleLogService } from './log.service';

@Injectable()
export class LogConsumerService implements OnModuleInit {
  private readonly logger = new Logger(LogConsumerService.name);

  constructor(
    private readonly rabbitMQService: RabbitMQService,
    private readonly articleLogService: ArticleLogService,
  ) {}

  async onModuleInit() {
    this.logger.log('启动RabbitMQ消息监听');
    await this.rabbitMQService.consume('log-queue', async (msg) => {
      this.logger.log(`接收到消息: ${JSON.stringify(msg)}`);

      // 这里写异步处理逻辑
      await this.handleMessage(msg);

      this.logger.log('消息处理完成');
    });
  }

  private async handleMessage(msg: any) {
    const dto = {
      articleId: msg.article_id ? msg.article_id : -1,
      userId: msg.user_id ? msg.user_id : -1,
      action: msg.action,
      msg: msg.msg ? msg.msg : null,
      content: msg.content,
    };
    await this.articleLogService.create(dto);
    Logger.log('日志写入成功');
  }
}
