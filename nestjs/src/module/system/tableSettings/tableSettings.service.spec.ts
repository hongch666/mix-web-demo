/* eslint-disable @typescript-eslint/no-explicit-any */

import { TableSettingsService } from "./tableSettings.service";

describe("TableSettingsService", () => {
  // Verify the expected behavior of this unit test
  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const repository = {
      findOne: jest.fn().mockResolvedValue(null),
      create: jest.fn((value) => value),
      save: jest
        .fn()
        .mockResolvedValue({ user_id: 7, table_key: "articles", columns: [] }),
    };
    const service = new TableSettingsService(
      repository as any,
      { info: jest.fn() } as any,
    );
    await expect(service.saveSettings(7, "articles", [])).resolves.toEqual({
      user_id: 7,
      table_key: "articles",
      columns: [],
    });
    expect(repository.create).toHaveBeenCalled();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const repository = { delete: jest.fn().mockResolvedValue({ affected: 1 }) };
    const logger = { info: jest.fn() };
    await new TableSettingsService(
      repository as any,
      logger as any,
    ).deleteSettings(7, "articles");
    expect(repository.delete).toHaveBeenCalledWith({
      user_id: 7,
      table_key: "articles",
    });
    expect(logger.info).toHaveBeenCalled();
  });
});
