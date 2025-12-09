import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ApiLog, ApiLogSchema } from './schema/api-log.schema';
import { ApiLogService } from './api-log.service';
import { ApiLogController } from './api-log.controller';
import { ApiLogConsumerService } from './api-log.consume.service';
import { RabbitMQModule } from 'src/modules/mq/mq.module';

@Module({
  imports: [
    MongooseModule.forFeature([{ name: ApiLog.name, schema: ApiLogSchema }]),
    RabbitMQModule,
  ],
  providers: [ApiLogService, ApiLogConsumerService],
  controllers: [ApiLogController],
  exports: [ApiLogService],
})
export class ApiLogModule {}
