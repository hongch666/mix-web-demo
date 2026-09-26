import { TestService } from "./test.service";

describe("TestService", () => {
  // Verify the expected behavior of this unit test
  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const result = await new TestService().getWelcomeMessage();
    expect(result.code).toBe(200);
    expect(result.data).toBeDefined();
  });
});
