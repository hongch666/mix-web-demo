import { Module } from '@nestjs/common';
import { NacosModule } from './nacos/nacos.module';
import { WordModule } from './word/word.module';

@Module({
  imports: [NacosModule, WordModule],
})
export class CommonModule {}
