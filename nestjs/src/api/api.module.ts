import { Module } from '@nestjs/common';
import { TestModule } from './test/test.module';
import { ArticleLogModule } from './article-log/article-log.module';
import { ApiLogModule } from './api-log/api-log.module';
import { DownloadModule } from './download/download.module';
import { UploadModule } from './upload/upload.module';

@Module({
  imports: [
    TestModule,
    ArticleLogModule,
    ApiLogModule,
    DownloadModule,
    UploadModule,
  ],
})
export class ApiModule {}
