import { Inject, Injectable } from '@nestjs/common';
import Redis from 'ioredis';
import { v4 as uuidv4 } from 'uuid';
import { Constants } from '../../common/utils/constants';

/**
 * 解锁 Lua 脚本：只有当锁的值与预期值一致时才删除，保证只有锁持有者才能解锁
 */
const UNLOCK_SCRIPT = `
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
else
  return 0
end
`;

@Injectable()
export class RedisService {
  private readonly redis: Redis | null;

  constructor(@Inject(Constants.REDIS_CLIENT) redis: Redis | null) {
    this.redis = redis;
  }

  /**
   * 获取 Redis 客户端实例（可能为 null，表示未配置 Redis）
   */
  getClient(): Redis | null {
    return this.redis;
  }

  /**
   * 尝试获取分布式锁
   * @param lockKey 锁的 Redis key
   * @param expireSeconds 锁的过期时间（秒），应大于任务执行时间，防止死锁
   * @returns 锁的唯一标识（UUID），获取失败返回 null（Redis 未配置时返回空字符串表示直接执行）
   */
  async tryLock(lockKey: string, expireSeconds: number): Promise<string | null> {
    if (!this.redis) {
      // Redis 未配置，返回空字符串表示单实例模式可直接执行
      return '';
    }

    const lockValue = uuidv4();
    const result = await this.redis.set(
      lockKey,
      lockValue,
      'EX',
      expireSeconds,
      'NX',
    );
    return result === 'OK' ? lockValue : null;
  }

  /**
   * 释放分布式锁（原子操作，只有锁持有者才能解锁）
   * @param lockKey 锁的 Redis key
   * @param lockValue 锁的唯一标识（加锁时返回的值）
   * @returns 是否成功释放
   */
  async unlock(lockKey: string, lockValue: string): Promise<boolean> {
    if (!this.redis) {
      return true;
    }

    const result = await this.redis.eval(
      UNLOCK_SCRIPT,
      1,
      lockKey,
      lockValue,
    );
    return result === 1;
  }
}
