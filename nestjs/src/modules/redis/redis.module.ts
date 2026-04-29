import { DynamicModule, Module, Provider } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import Redis from 'ioredis';
import { Constants } from '../../common/utils/constants';
import { RedisService } from './redis.service';

@Module({})
export class RedisModule {
  /**
   * 注册 Redis 模块，从 ConfigService 中读取 redis 配置段
   * 如果未配置 Redis，则跳过初始化
   */
  static forRoot(): DynamicModule {
    const redisClientProvider: Provider = {
      provide: Constants.REDIS_CLIENT,
      useFactory: (configService: ConfigService): Redis | null => {
        const redisConfig = configService.get('redis') as Record<string, unknown>;
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
    };

    return {
      module: RedisModule,
      imports: [ConfigModule],
      providers: [redisClientProvider, RedisService],
      exports: [RedisService],
      global: true,
    };
  }
}
