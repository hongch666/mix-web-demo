import { MongoTools, Messages } from "src/common/constants";
import { MongoToolsService } from "./mongoTools.service";

interface FakeMongoConnection {
  connection: never;
  aggregate: jest.Mock;
}

/** 构造只暴露 db.collection().aggregate().toArray() 的假连接 */
function createFakeConnection(result: unknown[] = []): FakeMongoConnection {
  const aggregate = jest.fn().mockReturnValue({
    toArray: jest.fn().mockResolvedValue(result),
  });
  const connection = {
    db: { collection: jest.fn().mockReturnValue({ aggregate }) },
  };
  return { connection: connection as never, aggregate };
}

describe("MongoToolsService", () => {
  // 验证不在白名单中的集合会被拒绝查询
  it("验证非法集合名称被拒绝", async () => {
    const service = new MongoToolsService({} as never);
    await expect(service.query("not_allowed", {}, 10)).rejects.toThrow();
  });

  // 验证聚合查询同样受 collection 白名单约束
  it("验证聚合查询拒绝非白名单集合", async () => {
    const { connection } = createFakeConnection();
    const service = new MongoToolsService(connection);

    await expect(
      service.aggregate("not_allowed", [{ $count: "total" }], 10),
    ).rejects.toThrow(Messages.MONGO_COLLECTION_NOT_ALLOWED_MSG("not_allowed"));
  });

  // 验证管道末尾缺少 $limit 时由服务端追加，避免聚合结果无限膨胀
  it("验证聚合管道自动追加结果条数上限", async () => {
    const { connection, aggregate } = createFakeConnection([
      { _id: "a", count: 2 },
    ]);
    const service = new MongoToolsService(connection);

    const result = await service.aggregate(
      "apilogs",
      [{ $group: { _id: "$path", count: { $sum: 1 } } }],
      20,
    );

    expect(result).toEqual([{ _id: "a", count: 2 }]);
    expect(aggregate).toHaveBeenCalledWith(
      [{ $group: { _id: "$path", count: { $sum: 1 } } }, { $limit: 20 }],
      {
        allowDiskUse: false,
        maxTimeMS: MongoTools.AGGREGATE_MAX_TIME_MS,
      },
    );
  });

  // 验证管道自带的 $limit 会被收紧到本次请求上限
  it("验证聚合管道自带的 $limit 被收紧", async () => {
    const { connection, aggregate } = createFakeConnection();
    const service = new MongoToolsService(connection);

    await service.aggregate("apilogs", [{ $limit: 500 }], 10);

    expect(aggregate).toHaveBeenCalledWith([{ $limit: 10 }], {
      allowDiskUse: false,
      maxTimeMS: MongoTools.AGGREGATE_MAX_TIME_MS,
    });
  });

  // 验证阶段白名单之外的阶段被拒绝
  it("验证未开放的聚合阶段被拒绝", async () => {
    const { connection, aggregate } = createFakeConnection();
    const service = new MongoToolsService(connection);

    await expect(
      service.aggregate(
        "apilogs",
        [
          {
            $lookup: {
              from: "articlelogs",
              localField: "id",
              foreignField: "id",
              as: "x",
            },
          },
        ],
        10,
      ),
    ).rejects.toThrow(
      Messages.MONGO_AGGREGATE_STAGE_NOT_ALLOWED_MSG("$lookup"),
    );
    expect(aggregate).not.toHaveBeenCalled();
  });

  // 验证单个阶段包含多个操作符时被拒绝
  it("验证多操作符阶段被拒绝", async () => {
    const { connection } = createFakeConnection();
    const service = new MongoToolsService(connection);

    await expect(
      service.aggregate("apilogs", [{ $match: {}, $limit: 5 }], 10),
    ).rejects.toThrow(Messages.MONGO_AGGREGATE_STAGE_NOT_ALLOWED_MSG("$match"));
  });

  // 验证危险操作符即使藏在聚合阶段内部也会被拒绝
  it("验证聚合阶段内的危险操作符被拒绝", async () => {
    const { connection } = createFakeConnection();
    const service = new MongoToolsService(connection);

    await expect(
      service.aggregate(
        "apilogs",
        [{ $match: { $expr: { $gt: ["$response_time", 200] } } }],
        10,
      ),
    ).rejects.toThrow(Messages.MONGO_FORBIDDEN_OPERATOR_MSG("$expr"));
  });

  // 验证聚合结果中的 ObjectId 被转换为可序列化字符串
  it("验证聚合结果中的 ObjectId 被序列化", async () => {
    const objectId = {
      _bsontype: "ObjectId",
      toString: () => "507f1f77bcf86cd799439011",
    };
    const { connection } = createFakeConnection([{ _id: objectId }]);
    const service = new MongoToolsService(connection);

    const result = await service.aggregate("apilogs", [{ $limit: 1 }], 10);

    expect(result).toEqual([{ _id: "507f1f77bcf86cd799439011" }]);
  });
});
