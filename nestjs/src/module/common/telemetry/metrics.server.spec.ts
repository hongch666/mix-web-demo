import { createServer } from "node:http";
import { MetricNames } from "src/common/constants";
import { metricsRegistry } from "./metrics";
import { startMetricsServer } from "./metrics.server";

jest.mock("node:http", () => ({
  createServer: jest.fn(() => ({ listen: jest.fn() })),
}));

interface MockResponse {
  writeHead: jest.Mock;
  setHeader: jest.Mock;
  end: jest.Mock;
}

interface MockServer {
  listen: jest.Mock;
}

type RequestHandler = (
  request: { url?: string },
  response: MockResponse,
) => void;

describe("startMetricsServer指标暴露服务", () => {
  const createServerMock: jest.Mock = createServer as unknown as jest.Mock;

  beforeEach(() => {
    createServerMock.mockClear();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // 等待一次宏任务, 让 response.end 所在的 Promise 链执行完成
  function flushAsync(): Promise<void> {
    return new Promise<void>((resolve) => setImmediate(resolve));
  }

  // 创建 writeHead 返回自身以支持 writeHead(状态码).end() 链式调用的响应替身
  function createResponse(): MockResponse {
    const writeHeadMock = jest.fn();
    const response: MockResponse = {
      writeHead: writeHeadMock,
      setHeader: jest.fn(),
      end: jest.fn(),
    };
    writeHeadMock.mockReturnValue(response);
    return response;
  }

  // 启动服务并取出注册到 createServer 的请求处理器, 同时校验监听地址
  function startServer(): { handler: RequestHandler; server: MockServer } {
    const returned = startMetricsServer(9464, "/metrics");
    const server = createServerMock.mock.results[0]?.value as MockServer;
    const handler = createServerMock.mock.calls[0]?.[0] as RequestHandler;

    expect(returned).toBe(server);
    expect(server.listen).toHaveBeenCalledWith(9464, "0.0.0.0");
    return { handler, server };
  }

  // 验证非指标路径直接返回 404, 不读取指标
  it("验证非指标路径返回404且不读取指标", () => {
    const metricsSpy = jest.spyOn(metricsRegistry, "metrics");
    const { handler } = startServer();
    const response = createResponse();

    handler({ url: "/health" }, response);

    expect(response.writeHead).toHaveBeenCalledWith(404);
    expect(response.end).toHaveBeenCalledTimes(1);
    expect(metricsSpy).not.toHaveBeenCalled();
  });

  // 验证指标路径按注册表内容类型输出指标文本
  it("验证指标路径返回指标内容与Content-Type", async () => {
    const { handler } = startServer();
    const response = createResponse();

    handler({ url: "/metrics" }, response);
    await flushAsync();

    expect(response.setHeader).toHaveBeenCalledWith(
      "Content-Type",
      metricsRegistry.contentType,
    );
    expect(response.end).toHaveBeenCalledWith(
      expect.stringContaining(MetricNames.HTTP_REQUESTS),
    );
  });

  // 验证指标读取失败时返回 500 而不是挂起连接
  it("验证指标读取失败时返回500", async () => {
    const { handler } = startServer();
    const response = createResponse();
    jest
      .spyOn(metricsRegistry, "metrics")
      .mockRejectedValueOnce(new Error("registry failure"));

    handler({ url: "/metrics" }, response);
    await flushAsync();

    expect(response.writeHead).toHaveBeenCalledWith(500);
    expect(response.end).toHaveBeenCalledTimes(1);
  });
});
