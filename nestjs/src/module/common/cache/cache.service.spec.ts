/* eslint-disable @typescript-eslint/no-explicit-any */

// uuid 为 ESM-only 包，jest-runtime 的 CJS require 无法加载，本测试只关心缓存逻辑，按单测规范在工厂中提供被用到的成员
jest.mock("uuid", () => ({ v4: () => "mocked-uuid" }));

import { Defaults, RedisKeys } from "src/common/constants";
import { LoggerService } from "src/module/common/logger/logger.service";
import { RedisService } from "src/module/common/redis/redis.service";
import { CacheService } from "./cache.service";

describe("CacheService", () => {
  const store = new Map<string, string>();
  const subscriber = {
    on: jest.fn(),
    subscribe: jest.fn().mockResolvedValue(undefined),
    quit: jest.fn().mockResolvedValue("OK"),
  };
  const redis = {
    get: jest.fn(async (key: string): Promise<string | null> => {
      return store.get(key) ?? null;
    }),
    set: jest.fn(async (key: string, value: string): Promise<string> => {
      store.set(key, value);
      return "OK";
    }),
    del: jest.fn(async (...keys: string[]): Promise<number> => {
      keys.forEach((key: string): boolean => store.delete(key));
      return keys.length;
    }),
    publish: jest.fn(async (): Promise<number> => 1),
    duplicate: jest.fn(() => subscriber),
  };
  const redisService = { getClient: () => redis } as unknown as RedisService;
  const loggerStub = {
    debug: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
  };
  const logger = loggerStub as unknown as LoggerService;

  /**
   * 创建被测缓存服务
   */
  function createService(): CacheService {
    return new CacheService(redisService, logger);
  }

  /**
   * 取出订阅回调，用于模拟其它实例广播失效通知
   */
  function getMessageHandler(): (channel: string, message: string) => void {
    const call: any[] | undefined = subscriber.on.mock.calls.find(
      (item: any[]): boolean => item[0] === "message",
    );
    return call?.[1] as (channel: string, message: string) => void;
  }

  beforeEach(() => {
    store.clear();
    jest.clearAllMocks();
  });

  it("重复读取命中 L1 本地缓存且不再访问 Redis", async () => {
    const service = createService();
    await service.set("table:settings:1:articles", { id: 1 });
    redis.get.mockClear();

    await expect(service.get("table:settings:1:articles")).resolves.toEqual({
      id: 1,
    });
    expect(redis.get).not.toHaveBeenCalled();
  });

  it("本地缓存为空时从 Redis 读取并回填到本地", async () => {
    const writer = createService();
    await writer.set("table:settings:1:all", [{ id: 1 }]);

    const reader = createService();
    await expect(reader.get("table:settings:1:all")).resolves.toEqual([
      { id: 1 },
    ]);
    expect(redis.get).toHaveBeenCalledWith("cache:table:settings:1:all");

    redis.get.mockClear();
    await expect(reader.get("table:settings:1:all")).resolves.toEqual([
      { id: 1 },
    ]);
    expect(redis.get).not.toHaveBeenCalled();
  });

  it("缓存 null 结果时返回 null 而不是未命中", async () => {
    const service = createService();
    await service.set("table:settings:1:missing", null);

    await expect(service.get("table:settings:1:missing")).resolves.toBeNull();
  });

  it("批量失效同时删除本地与 Redis 中的缓存并广播失效通知", async () => {
    const service = createService();
    await service.set("table:settings:1:articles", { id: 1 });
    await service.set("table:settings:1:all", [{ id: 1 }]);
    redis.publish.mockClear();

    await service.deleteMany([
      "table:settings:1:articles",
      "table:settings:1:all",
    ]);

    expect(redis.del).toHaveBeenCalledWith(
      "cache:table:settings:1:articles",
      "cache:table:settings:1:all",
    );
    expect(redis.publish).toHaveBeenCalledWith(
      RedisKeys.CACHE_INVALIDATE_CHANNEL,
      JSON.stringify(["table:settings:1:articles", "table:settings:1:all"]),
    );
    expect(RedisKeys.CACHE_INVALIDATE_CHANNEL).toBe("cache:invalidate:nestjs");
    await expect(service.get("table:settings:1:articles")).resolves.toBe(
      undefined,
    );
    await expect(service.get("table:settings:1:all")).resolves.toBe(undefined);
  });

  it("收到其它实例的失效通知后清理本地缓存", async () => {
    const service = createService();
    service.onModuleInit();
    await service.set("table:settings:1:articles", { id: 1 });

    const handler = getMessageHandler();
    expect(handler).toBeDefined();
    handler(
      RedisKeys.CACHE_INVALIDATE_CHANNEL,
      JSON.stringify(["table:settings:1:articles"]),
    );

    // 本地条目已被清理，读取会穿透到 Redis
    redis.get.mockClear();
    await expect(service.get("table:settings:1:articles")).resolves.toEqual({
      id: 1,
    });
    expect(redis.get).toHaveBeenCalled();

    await service.onModuleDestroy();
    expect(subscriber.quit).toHaveBeenCalled();
  });

  it("忽略无法解析的失效通知且不影响后续读写", async () => {
    const service = createService();
    service.onModuleInit();

    getMessageHandler()(RedisKeys.CACHE_INVALIDATE_CHANNEL, "not-json");

    expect(loggerStub.error).toHaveBeenCalled();
    await expect(service.get("table:settings:1:articles")).resolves.toBe(
      undefined,
    );
  });

  it("订阅失效频道失败时仍可按纯 L1 语义读写", async () => {
    redis.duplicate.mockImplementationOnce((): never => {
      throw new Error("duplicate failed");
    });
    const service = createService();

    service.onModuleInit();

    expect(loggerStub.error).toHaveBeenCalled();
    await service.set("table:settings:2:articles", { id: 2 });
    await expect(service.get("table:settings:2:articles")).resolves.toEqual({
      id: 2,
    });
  });

  it("Redis 未配置时退化为纯本地缓存", async () => {
    const service = new CacheService(
      { getClient: () => null } as unknown as RedisService,
      logger,
    );

    service.onModuleInit();
    await service.set("table:settings:2:articles", { id: 2 });
    await service.deleteMany(["table:settings:2:articles"]);

    await expect(service.get("table:settings:2:articles")).resolves.toBe(
      undefined,
    );
  });

  it("Redis 读取失败时按未命中处理并记录错误", async () => {
    const service = createService();
    redis.get.mockRejectedValueOnce(new Error("redis down"));

    await expect(service.get("table:settings:3:articles")).resolves.toBe(
      undefined,
    );
    expect(loggerStub.error).toHaveBeenCalled();
  });

  it("本地缓存条目数超过上限时淘汰最早写入的条目", async () => {
    const service = new CacheService(
      { getClient: () => null } as unknown as RedisService,
      logger,
    );
    const total: number = Defaults.CACHE_LOCAL_MAX_ENTRIES + 1;

    for (let index = 0; index < total; index += 1) {
      await service.set(`key-${index}`, index);
    }

    await expect(service.get("key-0")).resolves.toBeUndefined();
    await expect(service.get(`key-${total - 1}`)).resolves.toBe(total - 1);
  });

  it("L1 本地缓存按 5 分钟 TTL 过期", async () => {
    const service = new CacheService(
      { getClient: () => null } as unknown as RedisService,
      logger,
    );
    const now: number = Date.now();
    const nowSpy = jest.spyOn(Date, "now").mockReturnValue(now);

    try {
      await service.set("table:settings:ttl:articles", { id: 1 });
      await expect(service.get("table:settings:ttl:articles")).resolves.toEqual(
        { id: 1 },
      );

      nowSpy.mockReturnValue(
        now + (Defaults.CACHE_LOCAL_TTL_SECONDS + 1) * 1000,
      );
      await expect(
        service.get("table:settings:ttl:articles"),
      ).resolves.toBeUndefined();
    } finally {
      nowSpy.mockRestore();
    }
  });
});
