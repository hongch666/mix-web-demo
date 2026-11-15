import { Controller, Get, Query } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { ApiResponse, success } from "src/common/utils/response";
import {
  ApiResponseModel,
  SwaggerLogDeletionSyncData,
} from "src/common/utils/swaggerResponse";
import { RequireInternalToken } from "src/framework/decorators/requireInternalToken.decorator";
import { LogDeletionService } from "./logDeletion.service";

/**
 * 日志删除同步接口，仅供 FastAPI 数仓按游标拉取被删除日志的墓碑
 */
@Controller("log-deletions")
@ApiTags("日志删除同步模块")
export class LogDeletionController {
  constructor(private readonly logDeletionService: LogDeletionService) {}

  /**
   * 按 MongoDB ID 游标增量同步删除墓碑，供 FastAPI 数仓清除已删除日志
   */
  @Get("sync")
  @ApiOperation({
    summary: "游标同步日志删除墓碑",
    description:
      "供 FastAPI 数仓按 MongoDB ID 游标拉取被删除的 API 日志与文章日志墓碑，用于清除数仓中已删除的数据",
  })
  @RequireInternalToken()
  @ApiResponseModel({ data: SwaggerLogDeletionSyncData })
  async sync(
    @Query("cursor") cursor: string | undefined,
    @Query("limit") limit: string | undefined,
  ): Promise<ApiResponse<unknown>> {
    const data = await this.logDeletionService.findByCursor(
      cursor || null,
      Number(limit) || 1000,
    );
    return success(data);
  }
}
