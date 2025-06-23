import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { WordModule } from 'src/common/word/word.module';
import { NacosModule } from 'src/common/nacos/nacos.module';
import { UserService } from './user.service';
import { User } from './entities/user.entity';

@Module({
  imports: [TypeOrmModule.forFeature([User]), WordModule, NacosModule],
  controllers: [],
  providers: [UserService],
  exports: [UserService],
})
export class UserModule {}
