import { Injectable, OnModuleInit } from '@nestjs/common';
import { Constants } from 'src/common/utils/constants';
import { logger } from 'src/common/utils/writeLog';
import { RabbitMQService } from 'src/modules/mq/mq.service';
import { ApiLogService } from './api-log.service';
import { ApiLogMessage, CreateApiLogDto } from './dto/api-log.dto';

@Injectable()
export class ApiLogConsumerService implements OnModuleInit {
  constructor(
    private readonly rabbitMQService: RabbitMQService,
    private readonly apiLogService: ApiLogService,
  ) {}

  async onModuleInit() {
    logger.info(Constants.API_RABBITMQ_START);
    await this.rabbitMQService.consume(
      'api-log-queue',
      async (msg): Promise<void> => {
        try {
          // 处理两种消息格式：
          // 1. 对象
          // 2. JSON 字符串
          let apiLogData: ApiLogMessage;

          if (typeof msg === 'string') {
            // 如果是字符串，尝试解析为 JSON
            apiLogData = JSON.parse(msg) as ApiLogMessage;
            logger.info(`接收到 Spring 发送的 ApiLog 消息: ${String(msg)}`);
          } else {
            // 如果已是对象，直接使用
            apiLogData = msg as ApiLogMessage;
            logger.info(`接收到 ApiLog 消息: ${JSON.stringify(apiLogData)}`);
          }

          // 验证消息是否为 API 日志格式（必须包含 api_path 和 api_method）
          if (!apiLogData.api_path || !apiLogData.api_method) {
            logger.info(
              `收到非 API 日志格式的消息，已忽略: ${JSON.stringify(apiLogData)}`,
            );
            return;
          }

          // 转换为 DTO 格式
          let responseTime = apiLogData.response_time;
          if (responseTime < 0) {
            logger.warning(`接口响应时间为${responseTime}，已将其设置为0: `);
            responseTime = 0;
          }

          const dto: CreateApiLogDto = {
            userId: apiLogData.user_id,
            username: apiLogData.username || Constants.UNKNOWN_USERNAME,
            apiDescription: apiLogData.api_description,
            apiPath: apiLogData.api_path,
            apiMethod: apiLogData.api_method,
            queryParams: apiLogData.query_params,
            pathParams: apiLogData.path_params,
            requestBody: apiLogData.request_body,
            responseTime: responseTime,
          };

          // 保存到数据库
          await this.apiLogService.create(dto);
          logger.info(Constants.API_SAVE);
        } catch (error) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);
          logger.error(`处理 ApiLog 消息失败: ${errorMessage}`);
        }
      },
    );
  }
}
