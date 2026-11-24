import { Module } from "@nestjs/common";
import { CacheModule } from "./cache/cache.module";
import { ClientModule } from "./client/client.module";
import { GithubModule } from "./github/github.module";
import { LoggerModule } from "./logger/logger.module";
import { MailModule } from "./mail/mail.module";
import { NacosModule } from "./nacos/nacos.module";
import { RedisModule } from "./redis/redis.module";
import { TelemetryModule } from "./telemetry/telemetry.module";

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
