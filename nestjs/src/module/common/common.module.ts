import { Module } from "@nestjs/common";
import { ClientModule } from "./client/client.module";
import { GithubModule } from "./github/github.module";
import { LoggerModule } from "./logger/logger.module";
import { MailModule } from "./mail/mail.module";
import { TaskModule } from "./task/task.module";

@Module({
  imports: [LoggerModule, ClientModule, GithubModule, MailModule, TaskModule],
  exports: [ClientModule],
})
export class CommonModule {}
