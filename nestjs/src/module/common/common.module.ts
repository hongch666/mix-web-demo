import { Module } from "@nestjs/common";
import { ClientModule } from "./client/client.module";
import { GithubModule } from "./github/github.module";
import { LoggerModule } from "./logger/logger.module";
import { MailModule } from "./mail/mail.module";
import { TelemetryModule } from "./telemetry/telemetry.module";

/**
 * 公共模块，聚合客户端、GitHub 登录、邮件、遥测等通用能力
 */
@Module({
  imports: [
    TelemetryModule,
    LoggerModule,
    ClientModule,
    GithubModule,
    MailModule,
  ],
  exports: [ClientModule],
})
export class CommonModule {}
