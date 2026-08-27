import { Module } from "@nestjs/common";
import { ClientModule } from "./client/client.module";
import { GithubModule } from "./github/github.module";
import { MailModule } from "./mail/mail.module";
import { LoggerModule } from "./logger/logger.module";
import { NacosModule } from "./nacos/nacos.module";
import { OssModule } from "./oss/oss.module";
import { TaskModule } from "./task/task.module";
import { WordModule } from "./word/word.module";

@Module({
  imports: [
    ClientModule,
    GithubModule,
    LoggerModule,
    MailModule,
    NacosModule,
    TaskModule,
    WordModule,
    OssModule,
  ],
  exports: [
    ClientModule,
    GithubModule,
    LoggerModule,
    MailModule,
    NacosModule,
    TaskModule,
    WordModule,
    OssModule,
  ],
})
export class CommonModule {}
