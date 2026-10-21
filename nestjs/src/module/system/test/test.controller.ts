import { Controller, Get } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import {
  ApiResponseModel,
  SwaggerStringData,
} from "src/common/utils/swaggerResponse";
import { ApiResponse } from "src/common/utils/response";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
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
    summary: "NestJS自己的测试",
    description: "输出欢迎信息",
  })
  @ApiLog("测试NestJS服务")
  @ApiResponseModel({ data: SwaggerStringData })
  async getNestjs(): Promise<ApiResponse<string>> {
    return this.testService.getWelcomeMessage();
  }
}
