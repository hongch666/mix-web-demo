import { Module } from '@nestjs/common';
import { TestModule } from './test/test.module';
import { ArticleModule } from './article/article.module';
import { ArticleLogModule } from './log/log.module';

@Module({
  imports: [
    TestModule, // 测试模块
    ArticleModule, // 文章模块
    ArticleLogModule, // 文章日志模块
  ],
})
export class ApiModule {}
