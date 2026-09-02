import { Controller } from "@nestjs/common";
import { GrpcMethod } from "@nestjs/microservices";
import { Messages } from "src/common/constants";
import type { JsonRequest, Result } from "src/proto/common/result";
import { ApiLogService } from "src/module/system/apiLog/apiLog.service";
import { ArticleLogService } from "src/module/system/articleLog/articleLog.service";
import { MailService } from "../mail/mail.service";

type JsonObject = Record<string, unknown>;

function parsePayload(request: JsonRequest): JsonObject {
  if (!request?.payload?.length) return {};
  const value: unknown = JSON.parse(Buffer.from(request.payload).toString("utf8"));
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(Messages.GRPC_REQUEST_INVALID_PAYLOAD);
  }
  return value as JsonObject;
}

function result(data: unknown): Result {
  return {
    code: 200,
    message: Messages.GRPC_RESULT_SUCCESS,
    data: Buffer.from(JSON.stringify(data ?? null), "utf8"),
  };
}

function failure(error: unknown): Result {
  return {
    code: 500,
    message: error instanceof Error ? error.message : Messages.GRPC_REQUEST_FAILED,
    data: Buffer.from("null", "utf8"),
  };
}

@Controller()
export class GrpcController {
  constructor(
    private readonly articleLogService: ArticleLogService,
    private readonly apiLogService: ApiLogService,
    private readonly mailService: MailService,
  ) {}

  @GrpcMethod("Log", "SearchHistory")
  async searchHistory(request: JsonRequest): Promise<Result> {
    try {
      const payload = parsePayload(request);
      return result({ keywords: await this.articleLogService.getSearchHistory(Number(payload.user_id)) });
    } catch (error) {
      return failure(error);
    }
  }

  @GrpcMethod("Log", "ViewDistribution")
  async viewDistribution(request: JsonRequest): Promise<Result> {
    try {
      const payload = parsePayload(request);
      return result(await this.articleLogService.getViewDistribution(Number(payload.user_id)));
    } catch (error) {
      return failure(error);
    }
  }

  @GrpcMethod("Log", "SearchKeywords")
  async searchKeywords(request: JsonRequest): Promise<Result> {
    try {
      parsePayload(request);
      return result(await this.articleLogService.getSearchKeywords());
    } catch (error) {
      return failure(error);
    }
  }

  @GrpcMethod("Log", "ApiAverageSpeed")
  async apiAverageSpeed(request: JsonRequest): Promise<Result> {
    try {
      parsePayload(request);
      return result(await this.apiLogService.getApiAverageResponseTime());
    } catch (error) {
      return failure(error);
    }
  }

  @GrpcMethod("Log", "ApiCalledCount")
  async apiCalledCount(request: JsonRequest): Promise<Result> {
    try {
      parsePayload(request);
      return result(await this.apiLogService.getCalledCount());
    } catch (error) {
      return failure(error);
    }
  }

  @GrpcMethod("Email", "SendCode")
  async sendCode(request: JsonRequest): Promise<Result> {
    try {
      await this.mailService.sendVerificationCode(parsePayload(request) as never);
      return result(null);
    } catch (error) {
      return failure(error);
    }
  }
}
