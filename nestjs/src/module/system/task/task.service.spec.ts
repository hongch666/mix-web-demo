/* eslint-disable @typescript-eslint/no-explicit-any */

jest.mock("uuid", () => ({ v4: () => "unit-test-lock" }));

import { TaskService } from "./task.service";

/**
 * 构造 TaskService 测试实例，新增 OSS 清理与配置依赖均用桩替换
 */
function buildService(
  api: any,
  redis: any,
  ossCleanup: any = { cleanup: jest.fn() },
  config: any = { get: jest.fn().mockReturnValue(true) },
): TaskService {
  return new TaskService(
    api,
    redis,
    { info: jest.fn(), error: jest.fn(), warning: jest.fn() } as any,
    ossCleanup,
    config,
  );
}

describe("TaskService", () => {
  // 验证日志清理锁竞争时跳过执行
  it("API 日志清理锁竞争时跳过", async () => {
    const api = { cleanupOldLogs: jest.fn() };
    const redis = {
      tryLock: jest.fn().mockResolvedValue(null),
      unlock: jest.fn(),
    };
    await buildService(api, redis).cleanupOldApiLogs();
    expect(api.cleanupOldLogs).not.toHaveBeenCalled();
    expect(redis.unlock).not.toHaveBeenCalled();
  });

  // 验证获取锁后执行日志清理并释放锁
  it("获取锁后执行 API 日志清理并释放锁", async () => {
    const api = { cleanupOldLogs: jest.fn().mockResolvedValue(2) };
    const redis = {
      tryLock: jest.fn().mockResolvedValue("lock"),
      unlock: jest.fn().mockResolvedValue(true),
    };
    await buildService(api, redis).cleanupOldApiLogs();
    expect(api.cleanupOldLogs).toHaveBeenCalled();
    expect(redis.unlock).toHaveBeenCalledWith(expect.any(String), "lock");
  });

  // 验证 OSS 清理默认 dry-run：调用清理服务时传入 true
  it("OSS 清理默认以 dry-run 执行", async () => {
    const cleanup = { cleanup: jest.fn().mockResolvedValue(undefined) };
    const redis = {
      tryLock: jest.fn().mockResolvedValue("lock"),
      unlock: jest.fn().mockResolvedValue(true),
    };
    const config = { get: jest.fn().mockReturnValue(true) };
    await buildService({}, redis, cleanup, config).cleanupOssObjects();
    expect(cleanup.cleanup).toHaveBeenCalledWith(true);
  });

  // 验证显式关闭 dry-run 后执行真实删除
  it("配置 dry-run=false 时执行真实删除", async () => {
    const cleanup = { cleanup: jest.fn().mockResolvedValue(undefined) };
    const redis = {
      tryLock: jest.fn().mockResolvedValue("lock"),
      unlock: jest.fn().mockResolvedValue(true),
    };
    const config = { get: jest.fn().mockReturnValue(false) };
    await buildService({}, redis, cleanup, config).cleanupOssObjects();
    expect(cleanup.cleanup).toHaveBeenCalledWith(false);
  });

  // 验证 OSS 清理锁竞争时不调用清理服务
  it("OSS 清理锁竞争时跳过", async () => {
    const cleanup = { cleanup: jest.fn() };
    const redis = {
      tryLock: jest.fn().mockResolvedValue(null),
      unlock: jest.fn(),
    };
    await buildService({}, redis, cleanup).cleanupOssObjects();
    expect(cleanup.cleanup).not.toHaveBeenCalled();
  });
});
