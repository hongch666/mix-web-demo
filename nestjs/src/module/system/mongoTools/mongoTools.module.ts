import { Module } from "@nestjs/common";
import { MongoToolsController } from "./mongoTools.controller";
import { MongoToolsService } from "./mongoTools.service";

/**
 * MongoDB 工具模块，注册并导出受限日志查询服务
 */
@Module({
  providers: [MongoToolsService],
  controllers: [MongoToolsController],
  exports: [MongoToolsService],
})
export class MongoToolsModule {}
