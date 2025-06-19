import { Module } from '@nestjs/common';
import { RabbitMQModule } from './mq/mq.module';
import { NacosModule } from './nacos/nacos.module';
import { WordModule } from './word/word.module';

@Module({
  imports: [RabbitMQModule, NacosModule, WordModule],
})
export class CommonModule {}
