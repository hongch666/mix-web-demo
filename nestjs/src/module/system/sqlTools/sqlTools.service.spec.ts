import { DataSource } from "typeorm";
import { SqlToolsService } from "./sqlTools.service";

describe("SqlToolsService", () => {
  let query: jest.Mock;
  let service: SqlToolsService;

  beforeEach(() => {
    query = jest.fn();
    service = new SqlToolsService({ query } as unknown as DataSource);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it.each([
    ["空 SQL", "   "],
    ["写操作", "DELETE FROM user_table_settings LIMIT 1"],
    [
      "多条语句",
      "SELECT id FROM user_table_settings LIMIT 1; DROP TABLE users",
    ],
    ["非白名单表", "SELECT id FROM users LIMIT 1"],
    ["缺少 LIMIT", "SELECT id FROM user_table_settings"],
    ["LIMIT 超限", "SELECT id FROM user_table_settings LIMIT 101"],
  ])("拒绝%s且不访问数据库", async (_scenario, sql) => {
    await expect(service.executeQuery(sql, {})).rejects.toMatchObject({
      status: 400,
    });
    expect(query).not.toHaveBeenCalled();
  });

  it("按占位符出现顺序传递参数并映射结果", async () => {
    query.mockResolvedValue([{ user_id: 1, name: "alice" }]);

    await expect(
      service.executeQuery(
        "SELECT user_id, name FROM user_table_settings WHERE user_id = :id OR owner_id = :id AND name = :name LIMIT 10",
        { id: 1, name: "alice" },
      ),
    ).resolves.toEqual({
      columns: ["user_id", "name"],
      rows: [[1, "alice"]],
      rowCount: 1,
    });
    expect(query).toHaveBeenCalledWith(
      "SELECT user_id, name FROM user_table_settings WHERE user_id = ? OR owner_id = ? AND name = ? LIMIT 10",
      [1, 1, "alice"],
    );
  });

  it("允许单条 SQL 的结尾分号和字符串中的分号", async () => {
    query.mockResolvedValue([]);

    await expect(
      service.executeQuery(
        "SELECT id FROM user_table_settings WHERE name = 'a;b' LIMIT 1; ",
        {},
      ),
    ).resolves.toEqual({ columns: [], rows: [], rowCount: 0 });
    expect(query).toHaveBeenCalledWith(
      "SELECT id FROM user_table_settings WHERE name = 'a;b' LIMIT 1",
      [],
    );
  });

  it("数据库查询失败时返回服务错误", async () => {
    query.mockRejectedValue(new Error("database unavailable"));

    await expect(
      service.executeQuery("SELECT id FROM user_table_settings LIMIT 1", {}),
    ).rejects.toMatchObject({ status: 500 });
  });

  it("拒绝查询非白名单表的结构", async () => {
    await expect(service.getTables("users")).rejects.toMatchObject({
      status: 400,
    });
    expect(query).not.toHaveBeenCalled();
  });

  it("查询白名单表的字段结构", async () => {
    query.mockResolvedValue([
      { Field: "user_id", Type: "bigint", Key: "PRI", Comment: null },
    ]);

    await expect(service.getTables(" user_table_settings ")).resolves.toEqual({
      table: "user_table_settings",
      columns: [{ name: "user_id", type: "bigint", key: "PRI", comment: "" }],
    });
    expect(query).toHaveBeenCalledWith(
      "SHOW COLUMNS FROM `user_table_settings`",
    );
  });

  it("查询全部表时对单个表的失败返回 -1", async () => {
    query.mockRejectedValue(new Error("database unavailable"));

    await expect(service.getTables()).resolves.toEqual([
      { table: "user_table_settings", rowCount: -1 },
    ]);
    expect(query).toHaveBeenCalledWith(
      "SELECT COUNT(*) AS cnt FROM `user_table_settings` WHERE 1 LIMIT 1",
    );
  });
});
