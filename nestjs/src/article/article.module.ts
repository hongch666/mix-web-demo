import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ArticleController } from './article.controller';
import { ArticleService } from './article.service';
import { Articles } from './entities/article.entity';
import { WordModule } from 'src/word/word.module';

@Module({
  imports: [TypeOrmModule.forFeature([Articles]), WordModule],
  controllers: [ArticleController],
  providers: [ArticleService],
  exports: [ArticleService],
})
export class ArticleModule {}
