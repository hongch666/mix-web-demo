import { Body, Controller, Get, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { ApiResponse, success } from "src/common/utils/response";
import { RequireInternalToken } from "src/framework/decorators/requireInternalToken.decorator";
import { QueryMongoDto } from "./dto/mongoTools.dto";
import { MongoToolsService } from "./mongoTools.service";

@Controller("mongo-tools")
@ApiTags("MongoDB工具模块")
export class MongoToolsController {
  constructor(private readonly mongoToolsService: MongoToolsService) {}

  @Get("collections")
  @ApiOperation({
    summary: "列出日志集合",
    description: "列出白名单内日志集合及其基本信息，供 FastAPI 内部远程调用",
  })
  @RequireInternalToken()
  async listCollections(): Promise<ApiResponse<unknown>> {
    const data: unknown = await this.mongoToolsService.listCollections();
    return success(data);
  }

  @Post("query")
  @ApiOperation({
    summary: "查询日志文档",
    description: "对白名单内的日志集合执行只读查询，供 FastAPI 内部远程调用",
  })
  @RequireInternalToken()
  async query(@Body() dto: QueryMongoDto): Promise<ApiResponse<unknown>> {
    const data: unknown = await this.mongoToolsService.query(
      dto.collectionName,
      dto.filter ?? {},
      dto.limit ?? 10,
    );
    return success(data);
  }
}
