import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { RabbitMQModule } from 'src/modules/mq/mq.module';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { ApiLogConsumerService } from './api-log.consume.service';
import { ApiLogController } from './api-log.controller';
import { ApiLogService } from './api-log.service';
import { ApiLog, ApiLogSchema } from './schema/api-log.schema';

@Module({
  imports: [
    MongooseModule.forFeature([{ name: ApiLog.name, schema: ApiLogSchema }]),
    RabbitMQModule,
    NacosModule,
  ],
  providers: [ApiLogService, ApiLogConsumerService],
  controllers: [ApiLogController],
  exports: [ApiLogService],
})
export class ApiLogModule {}
