import { Module } from '@nestjs/common';
import { ClientModule } from 'src/modules/client/client.module';
import { TaskModule } from 'src/modules/task/task.module';
import { TestController } from './test.controller';

@Module({
  imports: [ClientModule, TaskModule],
  controllers: [TestController],
  providers: [],
})
export class TestModule {}
