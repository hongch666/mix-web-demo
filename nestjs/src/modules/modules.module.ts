import { Module } from '@nestjs/common';
import { ArticleModule } from './article/article.module';
import { UserModule } from './user/user.module';
import { NacosModule } from './nacos/nacos.module';
import { RabbitMQModule } from './mq/mq.module';
import { TaskModule } from './task/task.module';
import { WordModule } from './word/word.module';

@Module({
  imports: [
    ArticleModule,
    UserModule,
    NacosModule,
    RabbitMQModule,
    TaskModule,
    WordModule,
  ],
  exports: [
    ArticleModule,
    UserModule,
    NacosModule,
    RabbitMQModule,
    TaskModule,
    WordModule,
  ],
})
export class ModulesModule {}
