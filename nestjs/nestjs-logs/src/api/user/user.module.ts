import { Module } from '@nestjs/common';
import { NacosModule } from 'src/common/nacos/nacos.module';
import { UserService } from './user.service';

@Module({
  imports: [NacosModule],
  controllers: [],
  providers: [UserService],
  exports: [UserService],
})
export class UserModule {}
