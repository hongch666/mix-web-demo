import { Module } from '@nestjs/common';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { TaskModule } from 'src/modules/task/task.module';
import { TestController } from './test.controller';

@Module({
  imports: [NacosModule, TaskModule],
  controllers: [TestController],
  providers: [],
})
export class TestModule {}
