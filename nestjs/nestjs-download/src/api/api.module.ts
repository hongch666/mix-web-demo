import { Module } from '@nestjs/common';
import { ArticleModule } from './article/article.module';

@Module({
  imports: [
    ArticleModule, // 文章模块
  ],
})
export class ApiModule {}
