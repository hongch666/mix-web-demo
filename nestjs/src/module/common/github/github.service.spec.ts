jest.mock("uuid", () => ({ v4: () => "unit-test-lock" }));

import { GithubService } from "./github.service";

describe("GithubService", () => {
  // 验证缺少 OAuth 配置时拒绝生成授权地址
  it("验证缺少配置时拒绝生成授权地址", async () => {
    const service = new GithubService(
      { get: jest.fn().mockReturnValue({}) } as never,
      { getClient: jest.fn() } as never,
      {} as never,
      { error: jest.fn() } as never,
    );
    await expect(
      service.buildAuthorizeUrl({ redirect: "/home" }),
    ).rejects.toThrow();
  });
});
