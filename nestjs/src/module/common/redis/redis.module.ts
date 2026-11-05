import { Module } from "@nestjs/common";
import { ConfigModule, ConfigService } from "@nestjs/config";
import Redis from "ioredis";
import { RedisKeys } from "src/common/constants";
import { RedisService } from "./redis.service";

/**
 * Redis 模块，按配置创建 Redis 客户端并提供 RedisService
 *
 * 使用静态模块而非动态模块：provider 固定，使用方显式 imports 本模块即可注入 RedisService，
 * 不再依赖全局模块的隐式可见性；未配置 host/port 时 REDIS_CLIENT 为 null，RedisService 走降级实现
 */
@Module({
  imports: [ConfigModule],
  providers: [
    {
      provide: RedisKeys.REDIS_CLIENT,
      useFactory: (configService: ConfigService): Redis | null => {
        const redisConfig = configService.get("database.redis") as Record<
          string,
          unknown
        >;
        if (!redisConfig || !redisConfig.host || !redisConfig.port) {
          return null;
        }
        return new Redis({
          host: redisConfig.host as string,
          port: redisConfig.port as number,
          username: (redisConfig.username as string) || undefined,
          password: (redisConfig.password as string) || undefined,
          db: (redisConfig.db as number) || 0,
        });
      },
      inject: [ConfigService],
    },
    RedisService,
  ],
  exports: [RedisService],
})
export class RedisModule {}
