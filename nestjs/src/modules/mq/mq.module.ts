import { Module } from '@nestjs/common';
import { RabbitMQService } from './mq.service';

@Module({
  providers: [
    RabbitMQService
  ],
  exports: [
    RabbitMQService
  ],
})
export class RabbitMQModule {}
