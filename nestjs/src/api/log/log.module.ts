import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ArticleLog, ArticleLogSchema } from './schema/log.schema';
import { ArticleLogService } from './log.service';
import { ArticleLogController } from './log.controller';
import { LogConsumerService } from './log.consume.service';
import { RabbitMQModule } from 'src/common/mq/mq.module';
import { UserModule } from '../user/user.module';
import { ArticleModule } from '../article/article.module';

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
