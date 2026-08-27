import { Global, Module } from "@nestjs/common";
import { LoggerService } from "./logger.service";

/**
 * 全局日志模块
 *
 * 提供应用统一的日志服务，全局模块特性使得各层
 * 无需重复导入即可完成依赖注入
 */
@Global()
@Module({
  providers: [LoggerService],
  exports: [LoggerService],
})
export class LoggerModule {}
