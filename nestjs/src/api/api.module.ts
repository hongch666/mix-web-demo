import { Module } from '@nestjs/common';
import { AgentModule } from './agent/agent.module';
import { ApiLogModule } from './apiLog/apiLog.module';
import { ArticleLogModule } from './articleLog/articleLog.module';
import { DownloadModule } from './download/download.module';
import { GithubModule } from './github/github.module';
import { MailModule } from './mail/mail.module';
import { TestModule } from './test/test.module';
import { UploadModule } from './upload/upload.module';

@Module({
  imports: [
    TestModule,
    AgentModule,
    ArticleLogModule,
    ApiLogModule,
    DownloadModule,
    GithubModule,
    MailModule,
    UploadModule,
  ],
})
export class ApiModule {}
