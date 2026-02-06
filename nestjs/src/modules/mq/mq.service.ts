import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as amqp from 'amqplib';
import { logger } from '../../common/utils/writeLog';
import { Constants } from '../../common/utils/constants';

@Injectable()
export class RabbitMQService implements OnModuleInit, OnModuleDestroy {
  private connection: amqp.Connection;
  private channel: amqp.Channel;

  constructor(private readonly configService: ConfigService) {}

  async onModuleInit() {
    //获取配置对象
    const config = this.configService;
    //获取rabbitMQ相关配置
    const host = config.get<string>('rabbitmq.host');
    const port = config.get<number>('rabbitmq.port');
    const username = config.get<string>('rabbitmq.username');
    const password = config.get<string>('rabbitmq.password');
    const vhost = config.get<string>('rabbitmq.vhost');
    //连接RabbitMQ
    const url = `amqp://${username}:${password}@${host}:${port}${vhost === '/' ? '' : `/${vhost}`}`;
    this.connection = await amqp.connect(url);
    this.channel = await this.connection.createChannel();
    logger.info(Constants.RABBITMQ_CONNECTION);

    // 初始化时创建使用的队列
    await this.initializeQueues();
  }

  async onModuleDestroy() {
    await this.channel?.close();
    await this.connection?.close();
  }

  // 初始化时创建所有使用的队列
  private async initializeQueues() {
    const queues = [
      'api-log-queue', // API日志队列
      'log-queue',     // 通用日志队列
    ];

    for (const queue of queues) {
      try {
        await this.channel.assertQueue(queue, { durable: true });
        logger.info(`队列 [${queue}] 创建成功`);
      } catch (error) {
        logger.error(`创建队列 [${queue}] 失败: ${error.message}`);
        // 队列创建失败不应该阻止应用启动
      }
    }
  }

  // 生产者：发送消息
  async sendToQueue(queue: string, msg: any) {
    await this.channel.assertQueue(queue, { durable: true });
    this.channel.sendToQueue(queue, Buffer.from(JSON.stringify(msg)));
  }

  // 消费者：消费消息
  async consume(queue: string, onMessage: (msg: any) => void) {
    await this.channel.assertQueue(queue, { durable: true });
    this.channel.consume(queue, (msg) => {
      if (msg !== null) {
        const content = JSON.parse(msg.content.toString());
        onMessage(content);
        this.channel.ack(msg);
      }
    });
  }

  // 消费者：只消费1条消息
  async consumeOne(queue: string) {
    await this.channel.assertQueue(queue, { durable: true });
    const msg = await this.channel.get(queue, { noAck: false });
    if (msg) {
      const content = JSON.parse(msg.content.toString());
      this.channel.ack(msg);
      return content;
    }
    return null;
  }
}
