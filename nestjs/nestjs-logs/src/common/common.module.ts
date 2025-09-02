import { Module } from '@nestjs/common';
import { RabbitMQModule } from './mq/mq.module';
import { NacosModule } from './nacos/nacos.module';
import { TaskModule } from './task/task.module';

@Module({
  imports: [RabbitMQModule, NacosModule, TaskModule],
})
export class CommonModule {}
