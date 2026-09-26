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
});
