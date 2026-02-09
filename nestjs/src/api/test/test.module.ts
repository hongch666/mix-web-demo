import { Module } from '@nestjs/common';
import { TestController } from './test.controller';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { TaskModule } from 'src/modules/task/task.module';

@Module({
  imports: [NacosModule, TaskModule],
  controllers: [TestController],
  providers: [],
})
export class TestModule {}
