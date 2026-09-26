/* eslint-disable @typescript-eslint/no-explicit-any */

jest.mock("uuid", () => ({ v4: () => "unit-test-lock" }));

import { TaskService } from "./task.service";

describe("TaskService", () => {
  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const api = { cleanupOldLogs: jest.fn() };
    const article = { cleanupOldLogs: jest.fn() };
    const redis = {
      tryLock: jest.fn().mockResolvedValue(null),
      unlock: jest.fn(),
    };
    await new TaskService(
      api as any,
      article as any,
      redis as any,
      { info: jest.fn(), error: jest.fn() } as any,
    ).cleanupOldApiLogs();
    expect(api.cleanupOldLogs).not.toHaveBeenCalled();
    expect(redis.unlock).not.toHaveBeenCalled();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const article = { cleanupOldLogs: jest.fn().mockResolvedValue(2) };
    const redis = {
      tryLock: jest.fn().mockResolvedValue("lock"),
      unlock: jest.fn().mockResolvedValue(true),
    };
    await new TaskService(
      {} as any,
      article as any,
      redis as any,
      { info: jest.fn(), error: jest.fn() } as any,
    ).cleanupOldArticleLogs();
    expect(article.cleanupOldLogs).toHaveBeenCalled();
    expect(redis.unlock).toHaveBeenCalledWith(expect.any(String), "lock");
  });
});
