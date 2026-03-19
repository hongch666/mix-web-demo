import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ArticleModule } from 'src/modules/article/article.module';
import { RabbitMQModule } from 'src/modules/mq/mq.module';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { UserModule } from '../../modules/user/user.module';
import { LogConsumerService } from './article-log.consume.service';
import { ArticleLogController } from './article-log.controller';
import { ArticleLogService } from './article-log.service';
import { ArticleLog, ArticleLogSchema } from './schema/article-log.schema';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: ArticleLog.name, schema: ArticleLogSchema },
    ]),
    RabbitMQModule,
    UserModule,
    ArticleModule,
    NacosModule,
  ],
  providers: [ArticleLogService, LogConsumerService],
  controllers: [ArticleLogController],
  exports: [ArticleLogService],
})
export class ArticleLogModule {}
