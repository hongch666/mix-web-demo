import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { RedisModule } from "src/module/common/redis";
import { ApiLogModule } from "src/module/system/apiLog";
import { OssObjectModule } from "src/module/system/ossObject";
import { TaskController } from "./task.controller";
import { TaskService } from "./task.service";

/**
 * 定时任务模块，注册任务控制器与服务，聚合 API 日志与 OSS 对象清理能力并依赖 Redis 分布式锁
 */
@Module({
  imports: [ApiLogModule, RedisModule, OssObjectModule, ConfigModule],
  controllers: [TaskController],
  providers: [TaskService],
  exports: [TaskService],
})
export class TaskModule {}
