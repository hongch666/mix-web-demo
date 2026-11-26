import { Module } from "@nestjs/common";
import { CacheModule } from "src/module/common/cache";
import { ClientModule } from "src/module/common/client";
import { GithubModule } from "src/module/common/github";
import { LoggerModule } from "src/module/common/logger";
import { MailModule } from "src/module/common/mail";
import { NacosModule } from "src/module/common/nacos";
import { RedisModule } from "src/module/common/redis";
import { TelemetryModule } from "src/module/common/telemetry";

/**
 * 公共模块，集中加载系统级模块并导出根模块守卫所需的客户端与内部令牌工具
 */
@Module({
  imports: [
    TelemetryModule,
    LoggerModule,
    RedisModule,
    CacheModule,
    NacosModule,
    ClientModule,
    GithubModule,
    MailModule,
  ],
  exports: [ClientModule, NacosModule],
})
export class CommonModule {}
