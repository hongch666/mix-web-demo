import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ArticleLog, ArticleLogSchema } from './schema/article-log.schema';
import { ArticleLogService } from './article-log.service';
import { ArticleLogController } from './article-log.controller';
import { LogConsumerService } from './article-log.consume.service';
import { RabbitMQModule } from 'src/modules/mq/mq.module';
import { UserModule } from '../../modules/user/user.module';
import { ArticleModule } from 'src/modules/article/article.module';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: ArticleLog.name, schema: ArticleLogSchema },
    ]),
    RabbitMQModule,
    UserModule,
    ArticleModule,
  ],
  providers: [ArticleLogService, LogConsumerService],
  controllers: [ArticleLogController],
  exports: [ArticleLogService],
})
export class ArticleLogModule {}
