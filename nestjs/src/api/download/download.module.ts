import { Module } from '@nestjs/common';
import { DownloadController } from './download.controller';
import { DownloadService } from './download.service';
import { ArticleModule } from 'src/modules/article/article.module';
import { UserModule } from 'src/modules/user/user.module';
import { WordModule } from 'src/modules/word/word.module';
import { NacosModule } from 'src/modules/nacos/nacos.module';

@Module({
  imports: [
    ArticleModule, 
    UserModule, 
    WordModule, 
    NacosModule
  ],
  controllers: [
    DownloadController
  ],
  providers: [
    DownloadService
  ],
})
export class DownloadModule {}
