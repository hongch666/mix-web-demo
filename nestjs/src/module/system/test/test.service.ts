import { Injectable } from "@nestjs/common";
import { Messages } from "src/common/constants";
import { ApiResponse, success } from "src/common/utils/response";

/**
 * 测试服务
 *
 * 提供测试接口的示例数据组装，当前返回欢迎信息示例值
 */
@Injectable()
export class TestService {
  /**
   * 获取 NestJS 服务欢迎信息示例值
   */
  async getWelcomeMessage(): Promise<ApiResponse<string>> {
    return success(Messages.TEST_WELCOME);
  }
}
