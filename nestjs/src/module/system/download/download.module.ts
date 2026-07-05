import { Module } from '@nestjs/common';
import { ArticleModule } from 'src/module/common/article/article.module';
import { NacosModule } from 'src/module/common/nacos/nacos.module';
import { OssModule } from 'src/module/common/oss/oss.module';
import { UserModule } from 'src/module/common/user/user.module';
import { WordModule } from 'src/module/common/word/word.module';
import { DownloadController } from './download.controller';
import { DownloadService } from './download.service';

@Module({
  imports: [ArticleModule, UserModule, WordModule, NacosModule, OssModule],
  controllers: [DownloadController],
  providers: [DownloadService],
})
export class DownloadModule {}
