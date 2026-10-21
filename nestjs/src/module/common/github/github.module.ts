import { Module } from "@nestjs/common";
import { ClientModule } from "src/module/common/client/client.module";
import { RedisModule } from "src/module/common/redis/redis.module";
import { GithubController } from "./github.controller";
import { GithubService } from "./github.service";

/**
 * GitHub 登录模块，注册 GithubController 与 GithubService 并依赖 Redis 和服务调用客户端
 */
@Module({
  imports: [RedisModule, ClientModule],
  controllers: [GithubController],
  providers: [GithubService],
})
export class GithubModule {}
