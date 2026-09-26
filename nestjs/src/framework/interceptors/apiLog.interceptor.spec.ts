/* eslint-disable @typescript-eslint/no-explicit-any */

import { CallHandler, ExecutionContext } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { firstValueFrom, of } from "rxjs";
import { ApiLogInterceptor } from "./apiLog.interceptor";

describe("ApiLogInterceptor接口日志拦截器", () => {
  // 验证请求完成后会发布过滤敏感字段的接口日志
  it("验证请求完成后发布接口日志", async () => {
    const request = {
      method: "POST",
      url: "/users",
      body: { name: "alice", password: "secret" },
      params: { id: "7" },
      headers: {},
    };
    const reflector = {
      get: jest.fn().mockReturnValue({
        message: "更新用户",
        includeParams: true,
        excludeFields: ["password"],
      }),
    } as unknown as Reflector;
    const cls = {
      get: jest.fn((key: string) => ({ userId: 7, username: "alice" })[key]),
    };
    const amqp = { publish: jest.fn().mockResolvedValue(undefined) };
    const logger = { info: jest.fn(), error: jest.fn() };
    const context = {
      getHandler: () => function updateUser(): void {},
      switchToHttp: () => ({ getRequest: () => request }),
    } as unknown as ExecutionContext;
    const next: CallHandler = { handle: () => of("done") };

    await firstValueFrom(
      new ApiLogInterceptor(
        reflector,
        cls as any,
        amqp as any,
        logger as any,
      ).intercept(context, next),
    );
    await Promise.resolve();

    expect(amqp.publish).toHaveBeenCalledWith(
      "",
      "api-log-queue",
      expect.objectContaining({
        userId: 7,
        username: "alice",
        requestBody: { name: "alice" },
        pathParams: { id: "7" },
      }),
    );
  });
});
