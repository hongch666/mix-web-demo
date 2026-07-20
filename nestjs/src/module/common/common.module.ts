import { Module } from "@nestjs/common";
import { GithubModule } from "./github/github.module";
import { MailModule } from "./mail/mail.module";
import { NacosModule } from "./nacos/nacos.module";
import { OssModule } from "./oss/oss.module";
import { TaskModule } from "./task/task.module";
import { WordModule } from "./word/word.module";

@Module({
  imports: [
    GithubModule,
    MailModule,
    NacosModule,
    TaskModule,
    WordModule,
    OssModule,
  ],
  exports: [
    GithubModule,
    MailModule,
    NacosModule,
    TaskModule,
    WordModule,
    OssModule,
  ],
})
export class CommonModule {}
