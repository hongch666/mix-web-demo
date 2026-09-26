import { ConfigService } from "@nestjs/config";
import axios from "axios";
import type { NacosInstance } from "nacos";
import { ClsService } from "nestjs-cls";
import { HttpCode } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { InternalTokenUtil } from "src/common/utils/internalToken.util";
import { LoggerService } from "src/module/common/logger/logger.service";
import { NacosService } from "./nacos.service";

describe("NacosService", () => {
  afterEach(() => {
    for (const service of createdServices.splice(0)) {
      const state = service as unknown as {
        breakers: Map<string, { shutdown(): void }>;
      };
      for (const breaker of state.breakers.values()) {
        breaker.shutdown();
      }
    }
    jest.restoreAllMocks();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { service } = createService();
    jest.spyOn(service, "getServiceInstances").mockResolvedValue([]);
    const request = jest.spyOn(axios, "request");

    await expectBusinessStatus(
      service.call({
        serviceName: "spring",
        method: "GET",
        path: "/users/:id",
      }),
      HttpCode.SERVICE_UNAVAILABLE,
    );
    expect(request).not.toHaveBeenCalled();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { service, internalTokenUtil } = createService({
      userId: 7,
      username: "娴嬭瘯 alice",
      sessionId: "session-1",
      token: "access-token",
    });
    jest
      .spyOn(service, "getServiceInstances")
      .mockResolvedValue([instance("10.0.0.8", 8081)]);
    const request = jest.spyOn(axios, "request").mockResolvedValue({
      data: { code: HttpCode.OK, data: { id: 42 } },
    });

    const result = await service.call({
      serviceName: "spring",
      method: "POST",
      path: "/users/:id",
      pathParams: { id: "42" },
      queryParams: { source: "chat" },
      body: { enabled: true },
      headers: { "X-Custom": "custom" },
    });

    expect(result).toEqual({ code: HttpCode.OK, data: { id: 42 } });
    expect(internalTokenUtil.generateInternalToken).toHaveBeenCalledWith(
      7,
      "nestjs",
    );
    expect(request).toHaveBeenCalledWith(
      expect.objectContaining({
        url: "http://10.0.0.8:8081/users/42?source=chat",
        method: "POST",
        data: { enabled: true },
        timeout: 1000,
        proxy: false,
        headers: expect.objectContaining({
          "X-User-Id": "7",
          "X-Username": "alice",
          "X-Session-Id": "session-1",
          Authorization: "Bearer access-token",
          "X-Internal-Token": "Bearer internal-token",
          "X-Custom": "custom",
        }),
      }),
    );
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { service, internalTokenUtil } = createService();
    jest
      .spyOn(service, "getServiceInstances")
      .mockResolvedValue([instance("10.0.0.8", 8081)]);
    jest.spyOn(axios, "request").mockResolvedValue({
      data: { code: HttpCode.OK, data: null },
    });

    await service.call({
      serviceName: "spring",
      method: "GET",
      path: "/health",
    });

    expect(internalTokenUtil.generateInternalToken).toHaveBeenCalledWith(
      -1,
      "nestjs",
    );
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { service } = createService();
    jest
      .spyOn(service, "getServiceInstances")
      .mockResolvedValue([instance("10.0.0.8", 8081)]);
    jest.spyOn(axios, "request").mockResolvedValue({
      data: { code: HttpCode.BAD_REQUEST, msg: "invalid" },
    });

    await expectBusinessStatus(
      service.call({
        serviceName: "spring",
        method: "GET",
        path: "/resource",
      }),
      HttpCode.BAD_GATEWAY,
    );
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { service } = createService();
    jest
      .spyOn(service, "getServiceInstances")
      .mockResolvedValue([instance("10.0.0.8", 8081)]);
    const request = jest.spyOn(axios, "request");
    const state = service as unknown as {
      getBreaker(serviceName: string): { open(): void };
    };
    state.getBreaker("spring").open();

    const result = await service.call({
      serviceName: "spring",
      method: "GET",
      path: "/resource",
    });

    expect(result).toEqual({
      code: HttpCode.SERVICE_UNAVAILABLE,
      msg: expect.any(String),
      data: null,
    });
    expect(request).not.toHaveBeenCalled();
  });
});

type ContextValues = {
  userId?: number;
  username?: string;
  sessionId?: string;
  token?: string;
};

const createdServices: NacosService[] = [];

function createService(context: ContextValues = {}): {
  service: NacosService;
  internalTokenUtil: jest.Mocked<
    Pick<InternalTokenUtil, "generateInternalToken">
  >;
} {
  const configValues: Record<string, unknown> = {
    "server.serviceName": "nestjs",
  };
  const configService = {
    get: jest.fn((key: string) => configValues[key]),
  } as unknown as ConfigService;
  const cls = {
    get: jest.fn((key: keyof ContextValues) => context[key]),
  } as unknown as ClsService;
  const internalTokenUtil = {
    generateInternalToken: jest.fn().mockResolvedValue("internal-token"),
  };
  const logger = {
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
  } as unknown as LoggerService;
  const service = new NacosService(
    configService,
    cls,
    internalTokenUtil as unknown as InternalTokenUtil,
    logger,
  );
  const state = service as unknown as {
    remoteCallConfig: {
      timeout: number;
      maxRetries: number;
      initialBackoff: number;
      maxBackoff: number;
      circuitBreaker: {
        timeout: number;
        errorThresholdPercentage: number;
        resetTimeout: number;
        volumeThreshold: number;
      };
    };
  };
  state.remoteCallConfig = {
    timeout: 1000,
    maxRetries: 3,
    initialBackoff: 0,
    maxBackoff: 0,
    circuitBreaker: {
      timeout: 1000,
      errorThresholdPercentage: 50,
      resetTimeout: 1000,
      volumeThreshold: 1,
    },
  };
  createdServices.push(service);
  return { service, internalTokenUtil };
}

function instance(ip: string, port: number): NacosInstance {
  return { ip, port } as NacosInstance;
}

async function expectBusinessStatus(
  promise: Promise<unknown>,
  status: number,
): Promise<void> {
  try {
    await promise;
    throw new Error("鏈熸湜鎶涘嚭 BusinessException");
  } catch (error) {
    expect(error).toBeInstanceOf(BusinessException);
    expect((error as BusinessException).getStatus()).toBe(status);
  }
}
