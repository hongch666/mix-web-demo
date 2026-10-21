import { Module } from "@nestjs/common";
import { TestController } from "./test.controller";
import { TestService } from "./test.service";

/**
 * 测试模块，注册测试用控制器与服务
 */
@Module({
  controllers: [TestController],
  providers: [TestService],
})
export class TestModule {}
