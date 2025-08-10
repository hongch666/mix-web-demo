import { Module } from '@nestjs/common';
import { ArticleController } from './article.controller';
import { ArticleService } from './article.service';
import { WordModule } from 'src/common/word/word.module';
import { NacosModule } from 'src/common/nacos/nacos.module';
import { UserModule } from '../user/user.module';

@Module({
  imports: [WordModule, NacosModule, UserModule],
  controllers: [ArticleController],
  providers: [ArticleService],
  exports: [ArticleService],
})
export class ArticleModule {}
