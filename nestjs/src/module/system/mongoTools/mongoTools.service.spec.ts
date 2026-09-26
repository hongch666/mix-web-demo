import { MongoToolsService } from "./mongoTools.service";

describe("MongoToolsService", () => {
  // 验证不在白名单中的集合会被拒绝查询
  it("验证非法集合名称被拒绝", async () => {
    const service = new MongoToolsService({} as never);
    await expect(service.query("not_allowed", {}, 10)).rejects.toThrow();
  });
});
