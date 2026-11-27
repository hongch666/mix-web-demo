import { Controller, Get } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import {
  ApiResponse,
  ApiResponseModel,
  SwaggerStringData,
} from "src/common/utils";
import { ApiLog } from "src/framework/decorators";
import { TestService } from "./test.service";

/**
 * 测试接口，用于验证 NestJS 服务可用性
 */
@Controller("test")
@ApiTags("测试模块")
export class TestController {
  constructor(private readonly testService: TestService) {}

  /**
   * 返回 NestJS 服务的欢迎信息
   */
  @Get("nestjs")
  @ApiOperation({
    summary: "测试NestJS服务",
    description: "输出欢迎信息",
  })
  @ApiLog({ message: "测试NestJS服务", skipMq: true })
  @ApiResponseModel({ data: SwaggerStringData })
  async getNestjs(): Promise<ApiResponse<string>> {
    return this.testService.getWelcomeMessage();
  }
}
