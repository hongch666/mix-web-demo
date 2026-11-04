import { DynamicModule, Module } from "@nestjs/common";
import { DiscoveryModule } from "@nestjs/core";
import { CacheExplorer } from "./cache.explorer";
import { CacheService } from "./cache.service";

/**
 * 多级缓存模块，全局注册本地内存加 Redis 两级缓存服务与注解执行器
 */
@Module({})
export class CacheModule {
  /**
   * 注册缓存模块并全局导出 CacheService，依赖全局 RedisModule 提供的 RedisService
   */
  static forRoot(): DynamicModule {
    return {
      module: CacheModule,
      imports: [DiscoveryModule],
      providers: [CacheService, CacheExplorer],
      exports: [CacheService],
      global: true,
    };
  }
}
