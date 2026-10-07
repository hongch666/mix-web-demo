import {
  BadRequestException,
  CallHandler,
  ExecutionContext,
} from "@nestjs/common";
import { firstValueFrom, of, throwError } from "rxjs";
import {
  httpDuration,
  httpRequests,
} from "src/module/common/telemetry/metrics";
import { MetricsInterceptor } from "./metrics.interceptor";

describe("MetricsInterceptor接口指标拦截器", () => {
  const incMock = jest.fn();
  const observeMock = jest.fn();
  let requestLabelsSpy: jest.SpyInstance;
  let durationLabelsSpy: jest.SpyInstance;

  beforeEach(() => {
    incMock.mockClear();
    observeMock.mockClear();
    requestLabelsSpy = jest
      .spyOn(httpRequests, "labels")
      .mockReturnValue({ inc: incMock } as never);
    durationLabelsSpy = jest
      .spyOn(httpDuration, "labels")
      .mockReturnValue({ observe: observeMock } as never);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // 构造仅包含拦截器所需字段的 HTTP 执行上下文
  function buildContext(options: {
    method?: string;
    route?: string;
    statusCode?: number;
  }): ExecutionContext {
    const request = {
      method: options.method ?? "GET",
      routeOptions: options.route ? { url: options.route } : undefined,
    };
    const response = { statusCode: options.statusCode ?? 200 };
    return {
      switchToHttp: () => ({
        getRequest: () => request,
        getResponse: () => response,
      }),
    } as unknown as ExecutionContext;
  }

  // 验证请求正常结束时按响应状态码上报次数并记录耗时
  it("验证成功请求按响应状态码上报次数与耗时", async () => {
    const context = buildContext({
      method: "GET",
      route: "/users",
      statusCode: 201,
    });
    const next: CallHandler = { handle: () => of("ok") };

    const result = await firstValueFrom(
      new MetricsInterceptor().intercept(context, next),
    );

    expect(result).toBe("ok");
    expect(requestLabelsSpy).toHaveBeenCalledWith("GET", "/users", "201");
    expect(incMock).toHaveBeenCalledTimes(1);
    expect(durationLabelsSpy).toHaveBeenCalledWith("GET", "/users");
    expect(observeMock).toHaveBeenCalledTimes(1);
    expect(observeMock.mock.calls[0][0]).toBeGreaterThanOrEqual(0);
  });

  // 验证业务抛出的 HttpException 按异常状态码统计且耗时仍会上报
  it("验证HttpException错误按异常状态码统计", async () => {
    const context = buildContext({ method: "POST", route: "/users" });
    const next: CallHandler = {
      handle: () => throwError(() => new BadRequestException("参数错误")),
    };

    await expect(
      firstValueFrom(new MetricsInterceptor().intercept(context, next)),
    ).rejects.toThrow(BadRequestException);

    expect(requestLabelsSpy).toHaveBeenCalledWith("POST", "/users", "400");
    expect(incMock).toHaveBeenCalledTimes(1);
    expect(observeMock).toHaveBeenCalledTimes(1);
  });

  // 验证非 HttpException 错误统一按 500 统计
  it("验证非HttpException错误按500统计", async () => {
    const context = buildContext({ method: "PUT", route: "/articles" });
    const next: CallHandler = {
      handle: () => throwError(() => new Error("boom")),
    };

    await expect(
      firstValueFrom(new MetricsInterceptor().intercept(context, next)),
    ).rejects.toThrow("boom");

    expect(requestLabelsSpy).toHaveBeenCalledWith("PUT", "/articles", "500");
    expect(incMock).toHaveBeenCalledTimes(1);
    expect(observeMock).toHaveBeenCalledTimes(1);
  });

  // 验证路由信息缺失时使用 UNKNOWN 兜底标签, 避免指标标签为空
  it("验证路由信息缺失时使用UNKNOWN兜底", async () => {
    const context = buildContext({ method: "GET" });
    const next: CallHandler = { handle: () => of(null) };

    await firstValueFrom(new MetricsInterceptor().intercept(context, next));

    expect(requestLabelsSpy).toHaveBeenCalledWith("GET", "UNKNOWN", "200");
    expect(durationLabelsSpy).toHaveBeenCalledWith("GET", "UNKNOWN");
    expect(incMock).toHaveBeenCalledTimes(1);
    expect(observeMock).toHaveBeenCalledTimes(1);
  });
});
