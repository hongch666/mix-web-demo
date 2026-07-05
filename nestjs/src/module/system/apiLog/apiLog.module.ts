import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { NacosModule } from 'src/module/common/nacos/nacos.module';
import { ApiLogConsumerService } from './apiLog.consume.service';
import { ApiLogController } from './apiLog.controller';
import { ApiLogService } from './apiLog.service';
import { ApiLog, ApiLogSchema } from './schema/apiLog.schema';

@Module({
  imports: [
    MongooseModule.forFeature([{ name: ApiLog.name, schema: ApiLogSchema }]),
    NacosModule,
  ],
  providers: [ApiLogService, ApiLogConsumerService],
  controllers: [ApiLogController],
  exports: [ApiLogService],
})
export class ApiLogModule {}
