import { Module } from "@nestjs/common";
import { SqlToolsController } from "./sqlTools.controller";
import { SqlToolsService } from "./sqlTools.service";

/**
 * SQL 工具模块，注册并导出受限只读 SQL 查询服务
 */
@Module({
  controllers: [SqlToolsController],
  providers: [SqlToolsService],
  exports: [SqlToolsService],
})
export class SqlToolsModule {}
