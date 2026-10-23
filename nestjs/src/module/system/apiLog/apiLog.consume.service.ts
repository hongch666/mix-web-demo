import { RabbitSubscribe } from "@golevelup/nestjs-rabbitmq";
import { Injectable, OnApplicationShutdown } from "@nestjs/common";
import { Interval } from "@nestjs/schedule";
import { trace } from "@opentelemetry/api";
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

/**
 * 消费 RabbitMQ 的 API 日志消息并攒批写入 MongoDB
 */
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
   * 定时 flush 攒批缓冲：按 flushIntervalMs 周期触发，保证低并发下数据也能及时落库
   * buffer 为空时 flush() 会快速返回，无副作用
   */
  @Interval(Defaults.LOG_BATCH_FLUSH_INTERVAL_MS)
  async flushPendingLogs(): Promise<void> {
    // 定时 flush 没有请求入口，手动开启一段根 span，让批次日志关联到本次执行
    await trace
      .getTracer(Defaults.OTEL_TRACER_NAME)
      .startActiveSpan("job:api-log-flush", async (span) => {
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
   * 订阅 api-log-queue 消息，兼容对象与 JSON 字符串两种格式，归一化字段校验后入攒批队列
   */
  @RabbitSubscribe({
    queue: "api-log-queue",
  })
  async handleApiLog(msg: unknown): Promise<void> {
    // MQ 消费没有请求上下文，手动开启一段根 span，让消费日志关联到本次处理
    await trace
      .getTracer(Defaults.OTEL_TRACER_NAME)
      .startActiveSpan("mq:api-log-consume", async (span) => {
        try {
          await this.processApiLog(msg);
        } finally {
          span.end();
        }
      });
  }

  /**
   * 处理单条 API 日志消息：格式归一化、字段校验后入攒批队列
   */
  private async processApiLog(msg: unknown): Promise<void> {
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
