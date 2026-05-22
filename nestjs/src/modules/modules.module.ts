import { Module } from '@nestjs/common';
import { ArticleModule } from './article/article.module';
import { AppRabbitMQModule } from './mq/mq.module';
import { NacosModule } from './nacos/nacos.module';
import { OssModule } from './oss/oss.module';
import { TaskModule } from './task/task.module';
import { UserModule } from './user/user.module';
import { WordModule } from './word/word.module';

@Module({
  imports: [
    ArticleModule,
    UserModule,
    NacosModule,
    AppRabbitMQModule,
    TaskModule,
    WordModule,
    OssModule,
  ],
  exports: [
    ArticleModule,
    UserModule,
    NacosModule,
    AppRabbitMQModule,
    TaskModule,
    WordModule,
    OssModule,
  ],
})
export class ModulesModule {}
