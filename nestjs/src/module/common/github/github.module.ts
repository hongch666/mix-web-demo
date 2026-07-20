import { Module } from "@nestjs/common";
import { ClientModule } from "src/module/common/client/client.module";
import { RedisModule } from "src/module/common/redis/redis.module";
import { UserModule } from "src/module/system/user/user.module";
import { GithubController } from "./github.controller";
import { GithubService } from "./github.service";

@Module({
  imports: [UserModule, RedisModule, ClientModule],
  controllers: [GithubController],
  providers: [GithubService],
})
export class GithubModule {}
