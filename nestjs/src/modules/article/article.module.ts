import { Module } from '@nestjs/common';
import { ClientModule } from 'src/modules/client/client.module';
import { ArticleService } from './article.service';

@Module({
  imports: [ClientModule],
  providers: [ArticleService],
  exports: [ArticleService],
})
export class ArticleModule {}
