import { Injectable, OnModuleInit } from '@nestjs/common';
import { RabbitMQService } from 'src/common/mq/mq.service';
import { ApiLogService } from './api.log.service';
import { fileLogger } from 'src/common/utils/writeLog';
import { CreateApiLogDto } from './dto';

@Injectable()
export class ApiLogConsumerService implements OnModuleInit {
  constructor(
    private readonly rabbitMQService: RabbitMQService,
    private readonly apiLogService: ApiLogService,
  ) {}

  async onModuleInit() {
    fileLogger.info('启动 ApiLog RabbitMQ 消息监听');
    await this.rabbitMQService.consume('api-log-queue', async (msg) => {
      try {
        // ✨ 处理两种消息格式：
        // 1. NestJS 发送的对象
        // 2. Spring 发送的 JSON 字符串
        let apiLogData = msg;

        if (typeof msg === 'string') {
          // 如果是字符串，尝试解析为 JSON
          apiLogData = JSON.parse(msg);
          fileLogger.info(`接收到 Spring 发送的 ApiLog 消息: ${msg}`);
        } else {
          // 如果已是对象，直接使用
          fileLogger.info(`接收到 ApiLog 消息: ${JSON.stringify(apiLogData)}`);
        }

        // ✅ 验证消息是否为 API 日志格式（必须包含 api_path 和 api_method）
        if (!apiLogData.api_path || !apiLogData.api_method) {
          fileLogger.info(
            `收到非 API 日志格式的消息，已忽略: ${JSON.stringify(apiLogData)}`,
          );
          return;
        }

        // 转换为 DTO 格式
        const dto: CreateApiLogDto = {
          userId: apiLogData.user_id,
          username: apiLogData.username,
          apiDescription: apiLogData.api_description,
          apiPath: apiLogData.api_path,
          apiMethod: apiLogData.api_method,
          queryParams: apiLogData.query_params,
          pathParams: apiLogData.path_params,
          requestBody: apiLogData.request_body,
          responseTime: apiLogData.response_time,
        };

        // 保存到数据库
        await this.apiLogService.create(dto);
        fileLogger.info('API 日志已保存到数据库');
      } catch (error) {
        fileLogger.error(`处理 ApiLog 消息失败: ${error.message}`);
      }
    });
  }
}
