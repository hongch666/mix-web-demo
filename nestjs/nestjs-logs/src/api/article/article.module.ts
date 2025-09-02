import { Module } from '@nestjs/common';
import { ArticleService } from './article.service';
import { NacosModule } from 'src/common/nacos/nacos.module';

@Module({
  imports: [NacosModule],
  controllers: [],
  providers: [ArticleService],
  exports: [ArticleService],
})
export class ArticleModule {}
