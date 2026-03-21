import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ArticleModule } from 'src/modules/article/article.module';
import { RabbitMQModule } from 'src/modules/mq/mq.module';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { UserModule } from '../../modules/user/user.module';
import { LogConsumerService } from './articleLog.consume.service';
import { ArticleLogController } from './articleLog.controller';
import { ArticleLogService } from './articleLog.service';
import { ArticleLog, ArticleLogSchema } from './schema/articleLog.schema';

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
