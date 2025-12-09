import { Module } from '@nestjs/common';
import { TestController } from './test.controller';
import { NacosModule } from 'src/modules/nacos/nacos.module';

@Module({
  imports: [NacosModule],
  controllers: [TestController],
  providers: [],
})
export class TestModule {}
