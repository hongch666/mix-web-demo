import { Module } from '@nestjs/common';
import { NacosModule } from 'src/modules/nacos/nacos.module';
import { RedisModule } from 'src/modules/redis/redis.module';
import { UserModule } from 'src/modules/user/user.module';
import { GithubController } from './github.controller';
import { GithubService } from './github.service';

@Module({
  imports: [UserModule, RedisModule, NacosModule],
  controllers: [GithubController],
  providers: [GithubService],
})
export class GithubModule {}
