import "reflect-metadata";
import { ValidationPipe } from "@nestjs/common";
import { AggregateMongoDto } from "./mongoTools.dto";

// 全局 ValidationPipe 的实际配置：开启 transform 与隐式类型转换
const pipe = new ValidationPipe({
  transform: true,
  transformOptions: { enableImplicitConversion: true },
});

describe("AggregateMongoDto", () => {
  // 验证隐式转换不会清空聚合管道：阶段对象必须原样保留，否则阶段名会丢失
  it("验证聚合管道阶段在隐式转换后保持完整", async () => {
    const dto = (await pipe.transform(
      {
        collection_name: "apilogs",
        pipeline: [
          { $match: { response_time: { $gt: 200 } } },
          { $group: { _id: "$path", count: { $sum: 1 } } },
        ],
        limit: 5,
      },
      { type: "body" as const, metatype: AggregateMongoDto },
    )) as AggregateMongoDto;

    expect(dto.collectionName).toBe("apilogs");
    expect(dto.pipeline).toEqual([
      { $match: { response_time: { $gt: 200 } } },
      { $group: { _id: "$path", count: { $sum: 1 } } },
    ]);
    expect(dto.limit).toBe(5);
  });

  // 验证管道为空或超长时被请求校验拒绝
  it("验证空管道与超长管道被拒绝", async () => {
    await expect(
      pipe.transform(
        { collection_name: "apilogs", pipeline: [] },
        { type: "body" as const, metatype: AggregateMongoDto },
      ),
    ).rejects.toThrow();

    await expect(
      pipe.transform(
        {
          collection_name: "apilogs",
          pipeline: [1, 2, 3, 4, 5, 6, 7].map((item) => ({ $limit: item })),
        },
        { type: "body" as const, metatype: AggregateMongoDto },
      ),
    ).rejects.toThrow();
  });
});
