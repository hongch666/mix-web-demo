import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ArticleService } from './article.service';
import { Articles } from './entities/article.entity';
import { WordModule } from 'src/modules/word/word.module';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { User } from '../user/entities/user.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([Articles, User]),
    // WordModule,
    // NacosModule,
  ],
  providers: [ArticleService],
  exports: [ArticleService],
})
export class ArticleModule {}
