import { Controller, Get } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { ApiResponse } from "src/common/utils/response";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
import { TestService } from "./test.service";

@Controller("test")
@ApiTags("测试模块")
export class TestController {
  constructor(private readonly testService: TestService) {}

  @Get("nestjs")
  @ApiOperation({
    summary: "NestJS自己的测试",
    description: "输出欢迎信息",
  })
  @ApiLog("测试NestJS服务")
  async getNestjs(): Promise<ApiResponse<string>> {
    return this.testService.getWelcomeMessage();
  }
}
