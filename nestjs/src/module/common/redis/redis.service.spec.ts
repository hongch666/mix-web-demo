/* eslint-disable @typescript-eslint/no-explicit-any */

jest.mock("uuid", () => ({ v4: () => "unit-test-lock" }));

import { RedisService } from "./redis.service";

describe("RedisService", () => {
  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const service = new RedisService(null);
    await expect(service.tryLock("key", 10)).resolves.toBeNull();
    await expect(service.unlock("key", "value")).resolves.toBe(true);
    expect(service.getClient()).toBeNull();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const redis = { set: jest.fn().mockResolvedValue("OK") } as any;
    const value = await new RedisService(redis).tryLock("key", 10);
    expect(value).toEqual(expect.any(String));
    expect(redis.set).toHaveBeenCalledWith(
      "key",
      expect.any(String),
      "EX",
      10,
      "NX",
    );
  });

  // 未配置 Redis 时可用性为 false，且缓存读写与发布均为静默降级
  it("未配置 Redis 时封装方法静默降级", async () => {
    const service = new RedisService(null);

    expect(service.isAvailable()).toBe(false);
    await expect(service.getValue("cache:k")).resolves.toBeNull();
    await expect(service.setValue("cache:k", "v", 60)).resolves.toBeUndefined();
    await expect(service.deleteKeys(["cache:k"])).resolves.toBeUndefined();
    await expect(
      service.publish("channel", "message"),
    ).resolves.toBeUndefined();
    expect(service.subscribe("channel", jest.fn(), jest.fn())).toBeNull();
  });

  // 读取字符串值应直接透传 key，返回原始字符串
  it("getValue 透传 key 并返回原始字符串", async () => {
    const redis = { get: jest.fn().mockResolvedValue("payload") } as any;

    await expect(new RedisService(redis).getValue("cache:k")).resolves.toBe(
      "payload",
    );
    expect(redis.get).toHaveBeenCalledWith("cache:k");
  });

  // 写入字符串值时统一附加 EX 过期时间
  it("setValue 按秒设置 EX 过期时间", async () => {
    const redis = { set: jest.fn().mockResolvedValue("OK") } as any;

    await new RedisService(redis).setValue("cache:k", "payload", 300);

    expect(redis.set).toHaveBeenCalledWith("cache:k", "payload", "EX", 300);
  });

  // 批量删除应一次提交全部 key，空列表不发起命令
  it("deleteKeys 一次提交全部 key 且空列表跳过", async () => {
    const redis = { del: jest.fn().mockResolvedValue(2) } as any;
    const service = new RedisService(redis);

    await service.deleteKeys(["cache:a", "cache:b"]);
    await service.deleteKeys([]);

    expect(redis.del).toHaveBeenCalledTimes(1);
    expect(redis.del).toHaveBeenCalledWith("cache:a", "cache:b");
  });

  // 发布消息应透传频道与消息正文
  it("publish 透传频道与消息正文", async () => {
    const redis = { publish: jest.fn().mockResolvedValue(1) } as any;

    await new RedisService(redis).publish("cache:invalidate", '["k"]');

    expect(redis.publish).toHaveBeenCalledWith("cache:invalidate", '["k"]');
  });

  // 订阅应使用独立 duplicate 客户端并可通过句柄释放
  it("subscribe 使用独立客户端订阅并可通过句柄释放", async () => {
    const subscriber = {
      on: jest.fn(),
      subscribe: jest.fn().mockResolvedValue(1),
      quit: jest.fn().mockResolvedValue("OK"),
    };
    const redis = { duplicate: jest.fn(() => subscriber) } as any;
    const handler = jest.fn();
    const onError = jest.fn();

    const subscription = new RedisService(redis).subscribe(
      "channel",
      handler,
      onError,
    );

    expect(subscription).not.toBeNull();
    expect(redis.duplicate).toHaveBeenCalledTimes(1);
    expect(subscriber.on).toHaveBeenCalledWith("message", handler);
    expect(subscriber.subscribe).toHaveBeenCalledWith("channel");

    await subscription?.close();
    expect(subscriber.quit).toHaveBeenCalledTimes(1);
  });

  // 订阅命令异步失败时通过 onError 回调交给调用方记录日志
  it("subscribe 订阅失败时调用 onError 回调", async () => {
    const subscriber = {
      on: jest.fn(),
      subscribe: jest.fn().mockRejectedValue(new Error("boom")),
      quit: jest.fn(),
    };
    const redis = { duplicate: jest.fn(() => subscriber) } as any;
    const onError = jest.fn();

    new RedisService(redis).subscribe("channel", jest.fn(), onError);
    await new Promise<void>((resolve): void => {
      setImmediate(resolve);
    });

    expect(onError).toHaveBeenCalledTimes(1);
  });
});
