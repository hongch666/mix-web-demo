import { Module } from '@nestjs/common';
import { ArticleLogModule } from './log/log.module';

@Module({
  imports: [
    ArticleLogModule, // 文章日志模块
  ],
})
export class ApiModule {}
