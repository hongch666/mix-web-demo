jest.mock("@nestjs/microservices", () => ({
  GrpcMethod: () => () => undefined,
}));
jest.mock("src/module/system/articleLog/articleLog.service", () => ({
  ArticleLogService: class ArticleLogService {},
}));
jest.mock("src/module/system/apiLog/apiLog.service", () => ({
  ApiLogService: class ApiLogService {},
}));
jest.mock("src/module/common/mail/mail.service", () => ({
  MailService: class MailService {},
}));

import { GrpcController } from "./grpc.controller";

describe("GrpcController", () => {
  it("should adapt article log search history to common Result", async () => {
    const articleLogService = {
      getSearchHistory: jest.fn().mockResolvedValue(["nestjs", "grpc"]),
      getViewDistribution: jest.fn(),
      getSearchKeywords: jest.fn(),
    };
    const apiLogService = {
      getApiAverageResponseTime: jest.fn(),
      getCalledCount: jest.fn(),
    };
    const mailService = { sendVerificationCode: jest.fn() };
    const controller = new GrpcController(
      articleLogService as never,
      apiLogService as never,
      mailService as never,
    );

    const response = await controller.searchHistory({
      payload: Buffer.from(JSON.stringify({ user_id: 101 })),
    });

    expect(response.code).toBe(200);
    expect(JSON.parse(Buffer.from(response.data).toString("utf8"))).toEqual({
      keywords: ["nestjs", "grpc"],
    });
    expect(articleLogService.getSearchHistory).toHaveBeenCalledWith(101);
  });

  it("should return a business error Result when payload handling fails", async () => {
    const controller = new GrpcController(
      { getSearchHistory: jest.fn() } as never,
      {} as never,
      {} as never,
    );

    const response = await controller.searchHistory({
      payload: Buffer.from("[]"),
    });

    expect(response.code).toBe(500);
    expect(Buffer.from(response.data).toString("utf8")).toBe("null");
  });
});
