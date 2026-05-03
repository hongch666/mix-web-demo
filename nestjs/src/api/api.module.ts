import { Module } from '@nestjs/common';
import { ApiLogModule } from './apiLog/apiLog.module';
import { ArticleLogModule } from './articleLog/articleLog.module';
import { DownloadModule } from './download/download.module';
import { MailModule } from './mail/mail.module';
import { TestModule } from './test/test.module';
import { UploadModule } from './upload/upload.module';

@Module({
  imports: [
    TestModule,
    ArticleLogModule,
    ApiLogModule,
    DownloadModule,
    MailModule,
    UploadModule,
  ],
})
export class ApiModule {}
