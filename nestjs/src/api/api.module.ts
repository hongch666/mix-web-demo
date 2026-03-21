import { Module } from '@nestjs/common';
import { ApiLogModule } from './apiLog/apiLog.module';
import { ArticleLogModule } from './articleLog/articleLog.module';
import { DownloadModule } from './download/download.module';
import { TestModule } from './test/test.module';
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
