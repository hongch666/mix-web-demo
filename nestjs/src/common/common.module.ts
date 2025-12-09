import { Module } from '@nestjs/common';
import { RabbitMQModule } from '../modules/mq/mq.module';
import { NacosModule } from '../modules/nacos/nacos.module';
import { WordModule } from '../modules/word/word.module';
import { TaskModule } from '../modules/task/task.module';

@Module({
  imports: [RabbitMQModule, NacosModule, WordModule, TaskModule],
  exports: [RabbitMQModule], // ✨ 导出 RabbitMQModule，使其在全局范围可用
})
export class CommonModule {}
