import { Inject, Injectable } from "@nestjs/common";
import Redis from "ioredis";
import { RedisKeys } from "src/common/constants";
import { v4 as uuidv4 } from "uuid";

/** Redis Pub/Sub 消息处理器，接收频道与消息正文 */
export type RedisMessageHandler = (channel: string, message: string) => void;

/** Redis 订阅句柄，屏蔽底层 duplicate 客户端，便于调用方在模块销毁时释放 */
export interface RedisSubscription {
  /** 关闭订阅连接 */
  close(): Promise<void>;
}

/**
 * Redis 服务封装，提供客户端可用性判断、缓存读写、失效广播订阅与基于 set NX 及 Lua 脚本的分布式锁能力
 * 上层缓存组件只依赖本服务的业务级方法，不再直接调用 ioredis 命令
 */
@Injectable()
export class RedisService {
  private readonly redis: Redis | null;

  constructor(@Inject(RedisKeys.REDIS_CLIENT) redis: Redis | null) {
    this.redis = redis;
  }

  /**
   * 判断 Redis 客户端是否可用（未配置时为 false）
   */
  isAvailable(): boolean {
    return this.redis !== null;
  }

  /**
   * 获取 Redis 客户端实例（可能为 null，表示未配置 Redis）
   * 仅供需要原生命令的业务使用（如 OAuth 一次性状态），缓存读写请使用本服务封装方法
   */
  getClient(): Redis | null {
    return this.redis;
  }

  /**
   * 读取字符串值，未配置 Redis 或 key 不存在时返回 null
   */
  async getValue(key: string): Promise<string | null> {
    if (!this.redis) {
      return null;
    }
    return await this.redis.get(key);
  }

  /**
   * 写入字符串值并设置过期时间（秒），未配置 Redis 时静默跳过
   */
  async setValue(
    key: string,
    value: string,
    ttlSeconds: number,
  ): Promise<void> {
    if (!this.redis) {
      return;
    }
    await this.redis.set(key, value, "EX", ttlSeconds);
  }

  /**
   * 批量删除 key，未配置 Redis 或 key 列表为空时静默跳过
   */
  async deleteKeys(keys: string[]): Promise<void> {
    if (!this.redis || keys.length === 0) {
      return;
    }
    await this.redis.del(...keys);
  }

  /**
   * 向指定频道发布消息，未配置 Redis 时静默跳过
   */
  async publish(channel: string, message: string): Promise<void> {
    if (!this.redis) {
      return;
    }
    await this.redis.publish(channel, message);
  }

  /**
   * 订阅频道：使用独立的 duplicate 客户端，避免主客户端进入订阅模式后无法读写
   * 订阅命令的异步失败通过 onError 回调交给调用方记录日志，未配置 Redis 时返回 null
   */
  subscribe(
    channel: string,
    handler: RedisMessageHandler,
    onError: (error: unknown) => void,
  ): RedisSubscription | null {
    if (!this.redis || typeof this.redis.duplicate !== "function") {
      return null;
    }

    const subscriber: Redis = this.redis.duplicate();
    subscriber.on("message", handler);
    void subscriber.subscribe(channel).catch(onError);

    return {
      close: async (): Promise<void> => {
        await subscriber.quit();
      },
    };
  }

  /**
   * 尝试获取分布式锁
   * @param lockKey 锁的 Redis key
   * @param expireSeconds 锁的过期时间（秒），应大于任务执行时间，防止死锁
   * @returns 锁的唯一标识（UUID），获取失败或 Redis 未配置时返回 null
   */
  async tryLock(
    lockKey: string,
    expireSeconds: number,
  ): Promise<string | null> {
    if (!this.redis) {
      // Redis 未配置时无法保证分布式互斥，直接判定加锁失败
      return null;
    }

    const lockValue = uuidv4();
    const result = await this.redis.set(
      lockKey,
      lockValue,
      "EX",
      expireSeconds,
      "NX",
    );
    return result === "OK" ? lockValue : null;
  }

  /**
   * 释放分布式锁（原子操作，只有锁持有者才能解锁）
   * @param lockKey 锁的 Redis key
   * @param lockValue 锁的唯一标识
   * @returns 是否成功释放
   */
  async unlock(lockKey: string, lockValue: string): Promise<boolean> {
    if (!this.redis) {
      return true;
    }

    const result = await this.redis.eval(
      RedisKeys.UNLOCK_SCRIPT,
      1,
      lockKey,
      lockValue,
    );
    return result === 1;
  }
}
