import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ArticleService } from './article.service';
import { Articles } from './entities/article.entity';
import { User } from '../user/entities/user.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([Articles, User])
  ],
  providers: [
    ArticleService
  ],
  exports: [
    ArticleService
  ],
})
export class ArticleModule {}
