import { Module } from '@nestjs/common';
import { DownloadController } from './download.controller';
import { ArticleModule } from 'src/modules/article/article.module';

@Module({
  imports: [ArticleModule],
  controllers: [DownloadController],
})
export class DownloadModule {}
