import { Module } from "@nestjs/common";
import { DiscoveryModule } from "@nestjs/core";
import { CacheExplorer } from "src/framework/explorer/cache.explorer";
import { RedisModule } from "src/module/common/redis/redis.module";
import { CacheService } from "./cache.service";

/**
 * 多级缓存模块，注册本地内存加 Redis 两级缓存服务与注解执行器
 *
 * 不声明为全局模块：目前只有同模块的 CacheExplorer 注入 CacheService，
 * 业务侧通过 @Cacheable / @CacheEvict 注解由 CacheExplorer 织入即可，无需注入缓存服务；
 * 后续若有业务需要直接读写缓存，在自己的 imports 中显式引入本模块
 */
@Module({
  imports: [RedisModule, DiscoveryModule],
  providers: [CacheService, CacheExplorer],
  exports: [CacheService],
})
export class CacheModule {}
