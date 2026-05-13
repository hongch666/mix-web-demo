import { Module } from '@nestjs/common';
import { ClientModule } from 'src/modules/client/client.module';
import { RedisModule } from 'src/modules/redis/redis.module';
import { UserModule } from 'src/modules/user/user.module';
import { GithubController } from './github.controller';
import { GithubService } from './github.service';

@Module({
  imports: [UserModule, RedisModule, ClientModule],
  controllers: [GithubController],
  providers: [GithubService],
})
export class GithubModule {}
