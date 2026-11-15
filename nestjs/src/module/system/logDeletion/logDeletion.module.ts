import { Module } from "@nestjs/common";
import { MongooseModule } from "@nestjs/mongoose";
import { LogDeletionController } from "./logDeletion.controller";
import { LogDeletionService } from "./logDeletion.service";
import { LogDeletion, LogDeletionSchema } from "./schema/logDeletion.schema";

/**
 * 日志删除墓碑模块，注册墓碑集合、同步控制器与记录服务并导出服务
 */
@Module({
  imports: [
    MongooseModule.forFeature([
      { name: LogDeletion.name, schema: LogDeletionSchema },
    ]),
  ],
  providers: [LogDeletionService],
  controllers: [LogDeletionController],
  exports: [LogDeletionService],
})
export class LogDeletionModule {}
