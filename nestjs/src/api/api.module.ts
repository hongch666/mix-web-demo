import { Module } from '@nestjs/common';
import { TestModule } from './test/test.module';
import { ArticleLogModule } from './article-log/article-log.module';
import { ApiLogModule } from './api-log/api-log.module';
import { DownloadModule } from './download/download.module';

@Module({
  imports: [
    TestModule, // 测试模块
    ArticleLogModule, // 文章日志模块
    ApiLogModule, // API日志模块
    DownloadModule, // 下载模块
  ],
})
export class ApiModule {}
