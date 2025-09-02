import { Module } from '@nestjs/common';
import { WordModule } from 'src/common/word/word.module';
import { NacosModule } from 'src/common/nacos/nacos.module';
import { UserService } from './user.service';

@Module({
  imports: [WordModule, NacosModule],
  controllers: [],
  providers: [UserService],
  exports: [UserService],
})
export class UserModule {}
