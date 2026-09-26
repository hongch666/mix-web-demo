/* eslint-disable @typescript-eslint/no-explicit-any */

import { SqlToolsService } from "./sqlTools.service";

describe("SqlToolsService", () => {
  // Verify the expected behavior of this unit test
  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const service = new SqlToolsService({ query: jest.fn() } as any);
    await expect(service.executeQuery("", {})).rejects.toThrow();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const query = jest.fn().mockResolvedValue([{ user_id: 1 }]);
    const service = new SqlToolsService({ query } as any);
    await expect(
      service.executeQuery(
        "SELECT user_id FROM user_table_settings LIMIT 10",
        {},
      ),
    ).resolves.toEqual({
      columns: ["user_id"],
      rows: [[1]],
      rowCount: 1,
    });
    expect(query).toHaveBeenCalled();
  });
});
