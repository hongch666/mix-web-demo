/* eslint-disable @typescript-eslint/no-explicit-any */
import { CallHandler, ExecutionContext } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { firstValueFrom, of } from "rxjs";
import { ApiLogInterceptor } from "./apiLog.interceptor";

describe("ApiLogInterceptor接口日志拦截器", () => {
  // 验证请求完成后会发布过滤敏感字段的接口日志，且路径取路由模板而不是带参数值的实际路径
  it("验证请求完成后发布接口日志", async () => {
    const request = {
      method: "POST",
      url: "/users/7",
      routeOptions: { url: "/users/:id" },
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
        apiPath: "/users/:id",
        requestBody: { name: "alice" },
        pathParams: { id: "7" },
      }),
    );
  });

  // 验证未命中路由模板时退回不含查询串的原始路径
  it("验证路由模板缺失时退回原始路径", async () => {
    const request = {
      method: "GET",
      url: "/unknown/path?status=1",
      params: {},
      headers: {},
    };
    const reflector = {
      get: jest.fn().mockReturnValue({ message: "未匹配路由" }),
    } as unknown as Reflector;
    const cls = {
      get: jest.fn().mockReturnValue(undefined),
    };
    const amqp = { publish: jest.fn().mockResolvedValue(undefined) };
    const logger = { info: jest.fn(), error: jest.fn() };
    const context = {
      getHandler: () => function unknownRoute(): void {},
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
      expect.objectContaining({ apiPath: "/unknown/path" }),
    );
  });

  // 验证装饰器声明 skipMq 时不发布接口日志且业务结果照常返回
  it("验证跳过 MQ 时只保留本地日志", async () => {
    const request = {
      method: "POST",
      url: "/task/apilog",
      body: { name: "alice" },
      params: {},
      headers: {},
    };
    const reflector = {
      get: jest.fn().mockReturnValue({
        message: "内部清理任务",
        includeParams: true,
        skipMq: true,
      }),
    } as unknown as Reflector;
    const cls = {
      get: jest.fn((key: string) => ({ userId: 0, username: "internal" })[key]),
    };
    const amqp = { publish: jest.fn().mockResolvedValue(undefined) };
    const logger = { info: jest.fn(), error: jest.fn() };
    const context = {
      getHandler: () => function cleanupApiLog(): void {},
      switchToHttp: () => ({ getRequest: () => request }),
    } as unknown as ExecutionContext;
    const next: CallHandler = { handle: () => of("done") };

    const value = await firstValueFrom(
      new ApiLogInterceptor(
        reflector,
        cls as any,
        amqp as any,
        logger as any,
      ).intercept(context, next),
    );
    await Promise.resolve();

    expect(value).toBe("done");
    expect(amqp.publish).not.toHaveBeenCalled();
  });
});
