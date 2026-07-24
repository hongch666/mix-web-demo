import { RabbitSubscribe } from "@golevelup/nestjs-rabbitmq";
import { Injectable } from "@nestjs/common";
import { Messages } from "src/common/constants";
import { logger } from "src/common/utils/writeLog";
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
export class ApiLogConsumerService {
  constructor(private readonly apiLogService: ApiLogService) {}

  @RabbitSubscribe({
    queue: "api-log-queue",
  })
  async handleApiLog(msg: unknown): Promise<void> {
    try {
      logger.info(Messages.API_RABBITMQ_START);

      // 处理两种消息格式：
      // 1. 对象
      // 2. JSON 字符串
      let apiLogData: RawApiLogMessage;

      if (typeof msg === "string") {
        // 如果是字符串，尝试解析为 JSON
        apiLogData = JSON.parse(msg) as RawApiLogMessage;
        logger.info(Messages.API_LOG_SPRING_MESSAGE(String(msg)));
      } else {
        // 如果已是对象，直接使用
        apiLogData = msg as RawApiLogMessage;
        logger.info(Messages.API_LOG_MESSAGE(JSON.stringify(apiLogData)));
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
        logger.info(
          Messages.API_LOG_IGNORED_MESSAGE(JSON.stringify(apiLogData)),
        );
        return;
      }

      // 转换为 DTO 格式
      let responseTime = normalizedData.responseTime;
      if (responseTime < 0) {
        logger.warning(Messages.API_LOG_RESPONSE_TIME_CORRECTED(responseTime));
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

      // 保存到数据库
      await this.apiLogService.create(dto);
      logger.info(Messages.API_SAVE);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      logger.error(Messages.API_LOG_PROCESS_FAILED(errorMessage));
    }
  }
}
