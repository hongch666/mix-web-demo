/* eslint-disable @typescript-eslint/no-explicit-any */

import { SpringClientService } from "./springClient.service";

describe("SpringClientService", () => {
  // Verify the expected behavior of this unit test
  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const call = jest.fn().mockResolvedValue({ id: 7 });
    const service = new SpringClientService({ call } as any);
    await expect(service.getUserById(7)).resolves.toEqual({ id: 7 });
    expect(call).toHaveBeenCalled();
  });
});
