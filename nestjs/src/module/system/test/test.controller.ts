import { Controller, Get } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { Messages } from "src/common/constants";
import { ApiResponse, success } from "src/common/utils/response";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
import { FastapiClientService } from "src/module/common/client/fastapiClient.service";
import { GoZeroClientService } from "src/module/common/client/gozeroClient.service";
import { SpringClientService } from "src/module/common/client/springClient.service";

@Controller("api_nestjs")
@ApiTags("测试模块")
export class TestController {
  constructor(
    private readonly springClientService: SpringClientService,
    private readonly gozeroClientService: GoZeroClientService,
    private readonly fastapiClientService: FastapiClientService,
  ) {}

  @Get("nestjs")
  @ApiOperation({
    summary: "NestJS自己的测试",
    description: "输出欢迎信息",
  })
  @ApiLog("测试NestJS服务")
  async getNestjs(): Promise<ApiResponse<string>> {
    return success(Messages.TEST_WELCOME);
  }

  @Get("spring")
  @ApiOperation({
    summary: "调用Spring的测试",
    description: "输出欢迎信息",
  })
  @ApiLog("测试Spring服务")
  async getSpring(): Promise<ApiResponse<unknown>> {
    const res: Record<string, unknown> = await this.springClientService.test();
    return success(res.data);
  }

  @Get("gozero")
  @ApiOperation({
    summary: "调用GoZero的测试",
    description: "输出欢迎信息",
  })
  @ApiLog("测试GoZero服务")
  async getGin(): Promise<ApiResponse<unknown>> {
    const res: Record<string, unknown> = await this.gozeroClientService.test();
    return success(res.data);
  }

  @Get("fastapi")
  @ApiOperation({
    summary: "调用FastAPI的测试",
    description: "输出欢迎信息",
  })
  @ApiLog("测试FastAPI服务")
  async getFastAPI(): Promise<ApiResponse<unknown>> {
    const res: Record<string, unknown> = await this.fastapiClientService.test();
    return success(res.data);
  }
}
