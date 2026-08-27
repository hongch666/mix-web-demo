import { RabbitSubscribe } from "@golevelup/nestjs-rabbitmq";
import { Injectable, OnApplicationShutdown } from "@nestjs/common";
import { Interval } from "@nestjs/schedule";
import { Defaults, Messages } from "src/common/constants";
import { BatchBuffer } from "src/common/utils/batchBuffer";
import { LoggerService } from "src/module/common/logger/logger.service";
import { ApiLogService } from "./apiLog.service";
import { ApiLogMessage, ApiMethod, CreateApiLogDto } from "./dto/apiLog.dto";

type RawApiLogMessage = Partial<ApiLogMessage> & {
  user_id?: number;
  api_description?: string;
  api_path?: string;
  api_method?: ApiMethod;
  query_params?: Record<string, unknown>;
  path_params?: Record<string, unknown>;
  request_body?: Record<string, unknown> | string | null;
  response_time?: number;
};

@Injectable()
export class ApiLogConsumerService implements OnApplicationShutdown {
  private readonly batchBuffer: BatchBuffer<CreateApiLogDto>;

  constructor(
    private readonly apiLogService: ApiLogService,
    private readonly logger: LoggerService,
  ) {
    this.batchBuffer = new BatchBuffer<CreateApiLogDto>(
      "ApiLog",
      {
        batchSize: Defaults.LOG_BATCH_SIZE,
        flushIntervalMs: Defaults.LOG_BATCH_FLUSH_INTERVAL_MS,
        maxBufferSize: Defaults.LOG_BATCH_MAX_BUFFER_SIZE,
      },
      async (batch) => {
        await this.apiLogService.insertMany(batch);
      },
      logger,
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
    queue: "api-log-queue",
  })
  async handleApiLog(msg: unknown): Promise<void> {
    try {
      // 处理两种消息格式：
      // 1. 对象
      // 2. JSON 字符串
      let apiLogData: RawApiLogMessage;

      if (typeof msg === "string") {
        apiLogData = JSON.parse(msg) as RawApiLogMessage;
      } else {
        apiLogData = msg as RawApiLogMessage;
      }

      const normalizedData: ApiLogMessage = {
        userId: apiLogData.userId ?? apiLogData.user_id ?? 0,
        username: apiLogData.username || Messages.UNKNOWN_USERNAME,
        apiDescription:
          apiLogData.apiDescription ?? apiLogData.api_description ?? "",
        apiPath: apiLogData.apiPath ?? apiLogData.api_path ?? "",
        apiMethod: (apiLogData.apiMethod ?? apiLogData.api_method) as ApiMethod,
        queryParams: apiLogData.queryParams ?? apiLogData.query_params,
        pathParams: apiLogData.pathParams ?? apiLogData.path_params,
        requestBody: apiLogData.requestBody ?? apiLogData.request_body,
        responseTime: apiLogData.responseTime ?? apiLogData.response_time ?? 0,
      };

      // 验证消息是否为 API 日志格式（必须包含 apiPath 和 apiMethod）
      if (!normalizedData.apiPath || !normalizedData.apiMethod) {
        return;
      }

      // 转换为 DTO 格式
      let responseTime: number = normalizedData.responseTime;
      if (responseTime < 0) {
        responseTime = 0;
      }

      const dto: CreateApiLogDto = {
        userId: normalizedData.userId,
        username: normalizedData.username,
        apiDescription: normalizedData.apiDescription,
        apiPath: normalizedData.apiPath,
        apiMethod: normalizedData.apiMethod,
        queryParams: normalizedData.queryParams,
        pathParams: normalizedData.pathParams,
        requestBody:
          typeof normalizedData.requestBody === "string"
            ? { value: normalizedData.requestBody }
            : normalizedData.requestBody || undefined,
        responseTime: responseTime,
      };

      // 入队攒批
      this.batchBuffer.enqueue(dto);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      this.logger.error(Messages.API_LOG_PROCESS_FAILED(errorMessage));
    }
  }
}
