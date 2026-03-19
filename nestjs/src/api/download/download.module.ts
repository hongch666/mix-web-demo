import { Module } from '@nestjs/common';
import { DownloadController } from './download.controller';
import { DownloadService } from './download.service';
import { ArticleModule } from 'src/modules/article/article.module';
import { UserModule } from 'src/modules/user/user.module';
import { WordModule } from 'src/modules/word/word.module';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { OssModule } from 'src/modules/oss/oss.module';

@Module({
  imports: [ArticleModule, UserModule, WordModule, NacosModule, OssModule],
  controllers: [DownloadController],
  providers: [DownloadService],
})
export class DownloadModule {}
