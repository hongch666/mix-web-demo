import { Module } from '@nestjs/common';
import { TestController } from './test.controller';
import { NacosModule } from 'src/common/nacos/nacos.module';
import { SimpleLogger } from 'src/common/utils/writeLog';

@Module({
  imports: [NacosModule],
  controllers: [TestController],
  providers: [],
})
export class TestModule {}
