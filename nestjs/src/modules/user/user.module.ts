import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { WordModule } from 'src/modules/word/word.module';
import { User } from './entities/user.entity';
import { UserService } from './user.service';

@Module({
  imports: [TypeOrmModule.forFeature([User]), WordModule, NacosModule],
  controllers: [],
  providers: [UserService],
  exports: [UserService],
})
export class UserModule {}
