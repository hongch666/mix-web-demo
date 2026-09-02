import { Injectable, OnModuleInit } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import axios, { Method } from "axios";
import axiosRetry from "axios-retry";
import * as grpc from "@grpc/grpc-js";
import type { NacosInstance } from "nacos";
import { NacosNamingClient } from "nacos";
import { ClsService } from "nestjs-cls";
import CircuitBreaker from "opossum";
import * as os from "os";
import qs from "qs";
import { ErrorIds, HttpCode, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { InternalTokenUtil } from "src/common/utils/internalToken.util";
import { LoggerService } from "src/module/common/logger/logger.service";
import { ArticleService } from "src/proto/spring/article";
import { UserService } from "src/proto/spring/user";
import { JsonRequest, Result } from "src/proto/common/result";

interface CallOptions {
  serviceName: string;
  method: Method; // 'GET' | 'POST' | 'PUT' | 'DELETE'
  path: string;
  pathParams?: Record<string, string>;
  queryParams?: Record<string, string>;
  body?: Record<string, unknown>;
  headers?: Record<string, string>;
}

interface RemoteCallConfig {
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
}

@Injectable()
export class NacosService implements OnModuleInit {
  private client!: NacosNamingClient;

  // 使用 opossum 熔断器
  private readonly breakers = new Map<string, CircuitBreaker>();

  // 轮询负载均衡计数器
  private readonly roundRobinCounters = new Map<string, number>();

  // 远程调用配置
  private remoteCallConfig!: RemoteCallConfig;

  constructor(
    private readonly configService: ConfigService,
    private readonly cls: ClsService,
    private readonly internalTokenUtil: InternalTokenUtil,
    private readonly logger: LoggerService,
  ) {}

  async onModuleInit(): Promise<void> {
    // 加载远程调用配置
    this.remoteCallConfig =
      this.configService.get<RemoteCallConfig>("remote-call")!;

    // 配置 axios 重试机制
    axiosRetry(axios, {
      retries: this.remoteCallConfig.maxRetries,
      retryDelay: (retryCount: number) => {
        // 指数退避：使用配置的初始与最大退避时间
        return Math.min(
          this.remoteCallConfig.initialBackoff * Math.pow(2, retryCount - 1),
          this.remoteCallConfig.maxBackoff,
        );
      },
      retryCondition: (error) => {
        // 只对网络错误和 5xx 错误重试
        return (
          axiosRetry.isNetworkOrIdempotentRequestError(error) ||
          (error.response?.status !== undefined && error.response.status >= 500)
        );
      },
      onRetry: (retryCount, error) => {
        this.logger.warning(
          Messages.SERVICE_RETRY(
            error.config?.url || "unknown",
            retryCount,
            error.message,
          ),
        );
      },
    });

    // 取消终端与nacos相关的日志,如果需要日志可以将下面的logger设置为console
    const silentLogger: Record<string, (message?: unknown) => void> =
      Object.create(console);
    silentLogger.log = (): void => {};
    silentLogger.info = (): void => {};
    silentLogger.debug = (): void => {};
    silentLogger.warn = (): void => {};

    const nacosHost: string = this.configService.get<string>("nacos.host")!;
    if (!nacosHost) {
      throw BusinessException.internalServerError(
        Messages.NACOS_HOST_NOT_CONFIGURED,
      );
    }
    const nacosPort: string = this.configService.get<string>("nacos.port")!;
    if (!nacosPort) {
      throw BusinessException.internalServerError(
        Messages.NACOS_PORT_NOT_CONFIGURED,
      );
    }
    const nacosServerList: string = this.resolveNacosServerList(
      nacosHost,
      nacosPort,
    );
    const serverMode: string = this.configService
      .get<string>("server.mode")!
      .trim()
      .toLowerCase();
    if (!serverMode) {
      throw BusinessException.internalServerError(
        Messages.SERVER_MODE_NOT_CONFIGURED,
      );
    }

    this.client = new NacosNamingClient({
      logger: silentLogger,
      // Nacos 服务地址，默认端口为 8848
      serverList: nacosServerList,
      // 命名空间 ID
      namespace: this.configService.get<string>("nacos.namespace")!,
    });

    await this.client.ready();

    // 获取注册的 IP 地址，处理本地地址
    let registrationIp = this.configService.get<string>("server.ip")!;
    if (serverMode === "dev") {
      registrationIp = "127.0.0.1";
      this.logger.info(Messages.REGISTER_NACOS_DEV_MODE);
    } else if (
      !registrationIp ||
      registrationIp === "127.0.0.1" ||
      registrationIp === "0.0.0.0"
    ) {
      // 自动解析
      registrationIp = this.getLocalIp();
      this.logger.info(Messages.LOCAL_IP_CONVERTED(registrationIp));
    }

    // 注册当前服务
    await this.client.registerInstance(
      this.configService.get<string>("server.serviceName")!,
      {
        ip: registrationIp,
        port: this.configService.get<string>("server.port")!,
        weight: 1,
        ephemeral: true,
        clusterName: this.configService.get<string>("nacos.clusterName")!,
        serviceName: this.configService.get<string>("server.serviceName")!,
        enabled: true,
        healthy: true,
        metadata: {
          version: "1.0.0",
          ...(this.configService.get<boolean>("grpc.enabled")
            ? {
                grpc_port: String(this.configService.get<number>("grpc.port")),
                protocols: "grpc,http",
              }
            : { protocols: "http" }),
        },
      },
    );

    this.logger.info(Messages.REGISTER_NACOS);
  }

  /**
   * 获取本机 IP 地址
   */
  private getLocalIp(): string {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
      const networkInterface = interfaces[name];
      if (!networkInterface) continue;
      for (const addr of networkInterface) {
        // 获取第一个非本地地址的 IPv4 地址
        if (addr.family === "IPv4" && !addr.internal) {
          return addr.address;
        }
      }
    }
    // 如果没有找到，使用主机名
    return os.hostname();
  }

  /**
   * 组装 Nacos 服务地址，兼容：
   * 1. host + port
   * 2. 已经写成 host:port 的 host 配置
   */
  private resolveNacosServerList(host: string, port: string): string {
    const trimmedHost = host.trim();
    const trimmedPort = port.trim() || "8848";

    if (trimmedHost.includes(":") && !trimmedHost.startsWith("[")) {
      return trimmedHost;
    }

    return `${trimmedHost}:${trimmedPort}`;
  }

  async getServiceInstances(serviceName: string): Promise<NacosInstance[]> {
    const instances: NacosInstance[] =
      await this.client.getAllInstances(serviceName);
    return instances;
  }

  private getBreaker(serviceName: string): CircuitBreaker {
    const existing: CircuitBreaker | undefined = this.breakers.get(serviceName);
    if (existing) {
      return existing;
    }

    // 创建 opossum 熔断器，使用配置值
    const cbConfig = this.remoteCallConfig.circuitBreaker;
    const breaker = new CircuitBreaker(async (fn: () => Promise<any>) => fn(), {
      timeout: cbConfig.timeout, // 请求超时时间
      errorThresholdPercentage: cbConfig.errorThresholdPercentage, // 错误率阈值
      resetTimeout: cbConfig.resetTimeout, // 熔断器重置时间
      volumeThreshold: cbConfig.volumeThreshold, // 最小请求数
    });

    // 监听熔断器事件
    breaker.on("open", () => {
      this.logger.warning(Messages.SERVICE_CIRCUIT_BREAKER_OPEN(serviceName));
    });

    breaker.on("halfOpen", () => {
      this.logger.info(Messages.SERVICE_CIRCUIT_BREAKER_HALF_OPEN(serviceName));
    });

    breaker.on("close", () => {
      this.logger.info(Messages.SERVICE_CIRCUIT_BREAKER_CLOSE(serviceName));
    });

    breaker.on("fallback", (result: unknown) => {
      this.logger.warning(
        Messages.SERVICE_CIRCUIT_BREAKER_FALLBACK(serviceName, result),
      );
    });

    this.breakers.set(serviceName, breaker);
    return breaker;
  }

  async call(opts: CallOptions): Promise<Record<string, unknown>> {
    const grpcResult: Record<string, unknown> | null = await this.callGrpc(opts);
    if (grpcResult !== null) {
      return grpcResult;
    }
    const breaker = this.getBreaker(opts.serviceName);

    const instances: NacosInstance[] = await this.getServiceInstances(
      opts.serviceName,
    );
    if (!instances || instances.length === 0) {
      throw BusinessException.serviceUnavailable(
        Messages.SERVICE_NO_AVAILABLE_INSTANCE(opts.serviceName),
        ErrorIds.NO_AVAILABLE_SERVICE_INSTANCE,
      );
    }

    // 负载均衡策略：轮询
    const currentIndex = this.roundRobinCounters.get(opts.serviceName) || 0;
    const instance: NacosInstance = instances[currentIndex % instances.length]!;
    this.roundRobinCounters.set(opts.serviceName, currentIndex + 1);

    // 替换 pathParams
    let path: string = opts.path;
    if (opts.pathParams) {
      for (const [key, value] of Object.entries(opts.pathParams)) {
        path = path.replace(`:${key}`, value);
      }
    }

    // 拼接 URL
    const queryString: string = opts.queryParams
      ? `?${qs.stringify(opts.queryParams)}`
      : "";
    const url: string = `http://${instance.ip}:${instance.port}${path}${queryString}`;

    // 默认请求头
    const userId: number = this.cls.get<number>("userId") || 0;
    const userName: string = this.cls.get<string>("username") || "";
    const sessionId: string = this.cls.get<string>("sessionId") || "";
    const token: string = this.cls.get<string>("token") || "";
    // 将非 ASCII 字符替换为安全字符（RFC 7230 要求 header 值为 ASCII）
    const safeUserName: string =
      userName.replace(/[^\x20-\x7E]/g, "").trim() || "system";
    const defaultHeaders: Record<string, string> = {
      "X-User-Id": String(userId || 0),
      "X-Username": safeUserName,
      "X-Session-Id": sessionId,
    };
    if (token) {
      defaultHeaders["Authorization"] = `Bearer ${token}`;
    }

    // 生成并添加内部服务令牌 (没有用户ID时用-1代表系统调用)
    const finalUserId: number = userId > 0 ? userId : -1;
    const internalToken: string =
      await this.internalTokenUtil.generateInternalToken(
        finalUserId,
        this.configService.get<string>("server.serviceName")!,
      );
    defaultHeaders["X-Internal-Token"] = `Bearer ${internalToken}`;

    // 合并默认请求头和自定义请求头
    const headers: Record<string, string> = {
      ...defaultHeaders,
      ...(opts.headers || {}),
    };

    try {
      // 使用熔断器包装请求
      const response = await breaker.fire(async () => {
        const res = await axios.request({
          url,
          method: opts.method,
          data: opts.body,
          headers,
          timeout: this.remoteCallConfig.timeout,
        });

        // 校验业务响应码
        const responseData: Record<string, unknown> = res.data;
        if (responseData.code !== HttpCode.OK) {
          const errorMsg: string =
            (responseData.msg as string) || Messages.UNKNOWN_ERROR;
          this.logger.error(
            Messages.SERVICE_BUSINESS_ERROR_DETAIL(
              opts.serviceName,
              String(responseData.code),
              errorMsg,
            ),
          );
          throw BusinessException.badGateway(
            Messages.SERVICE_CALL_FAILED_WITH_MSG(opts.serviceName, errorMsg),
            ErrorIds.SERVICE_CALL_FAILED,
          );
        }

        return responseData;
      });

      return response as Record<string, unknown>;
    } catch (err) {
      // 熔断器降级处理
      if (err instanceof Error && err.message === "Breaker is open") {
        this.logger.warning(
          Messages.SERVICE_CIRCUIT_BREAKER_TRIGGERED(opts.serviceName),
        );
        return {
          code: HttpCode.SERVICE_UNAVAILABLE,
          msg: Messages.SERVICE_DEGRADED_MSG(opts.serviceName),
          data: null,
        };
      }

      this.logger.error(
        Messages.SERVICE_CALL_ERROR(
          opts.serviceName,
          err instanceof Error ? err.message : String(err),
        ),
      );
      throw BusinessException.badGateway(
        Messages.SERVICE_CALL_FAILED_RETRY_LATER(opts.serviceName),
        ErrorIds.SERVICE_CALL_FAILED,
      );
    }
  }

  /**
   * 调用已登记的 Spring gRPC 查询接口。返回 null 表示该路由或实例不支持，
   * 由上层继续使用原 HTTP 调用；业务错误不会静默降级。
   */
  private async callGrpc(
    opts: CallOptions,
  ): Promise<Record<string, unknown> | null> {
    const grpcEnabled: boolean = this.configService.get<boolean>("grpc.enabled") ?? false;
    const route = this.springGrpcRoute(opts.method, opts.path);
    if (!grpcEnabled || route === null) return null;

    let instances: NacosInstance[];
    try {
      instances = await this.getServiceInstances(opts.serviceName);
    } catch (error) {
      this.logger.warning(Messages.GRPC_CALL_FALLBACK(opts.serviceName, opts.path));
      return null;
    }
    const instance: NacosInstance | undefined = instances.find((item) => {
      const metadata = item.metadata as Record<string, string> | undefined;
      return Boolean(metadata?.grpc_port && metadata.protocols?.includes("grpc"));
    });
    if (!instance) return null;

    const metadata = new grpc.Metadata();
    const userId: number = this.cls.get<number>("userId") || 0;
    const username: string = this.cls.get<string>("username") || "";
    const sessionId: string = this.cls.get<string>("sessionId") || "";
    metadata.set("x-user-id", String(userId));
    metadata.set("x-username", username.replace(/[^\x20-\x7E]/g, "").trim());
    metadata.set("x-session-id", sessionId);
    const internalToken: string = await this.internalTokenUtil.generateInternalToken(
      userId > 0 ? userId : -1,
      this.configService.get<string>("server.serviceName")!,
    );
    metadata.set("x-internal-token", `Bearer ${internalToken}`);
    const grpcPort: string = (instance.metadata as Record<string, string> | undefined)?.grpc_port || "";
    const client = new grpc.Client(`${instance.ip}:${grpcPort}`, grpc.credentials.createInsecure());
    const payload: JsonRequest = {
      payload: Buffer.from(JSON.stringify({
        method: opts.method,
        route: opts.path,
        query: opts.queryParams || {},
        body: opts.body || null,
      }), "utf8"),
    };
    try {
      const response: Result = await new Promise<Result>((resolve, reject) => {
        client.makeUnaryRequest(
          route.path,
          (value: JsonRequest) => Buffer.from(JsonRequest.encode(value).finish()),
          (value: Buffer) => Result.decode(value),
          payload,
          metadata,
          { deadline: Date.now() + this.remoteCallConfig.timeout },
          (error: grpc.ServiceError | null, value?: Result) => error ? reject(error) : resolve(value!),
        );
      });
      const data: unknown = response.data?.length
        ? JSON.parse(Buffer.from(response.data).toString("utf8"))
        : null;
      const result: Record<string, unknown> = {
        code: response.code,
        msg: response.message,
        data,
      };
      if (response.code !== HttpCode.OK) {
        throw BusinessException.badGateway(
          Messages.SERVICE_CALL_FAILED_WITH_MSG(opts.serviceName, response.message),
          ErrorIds.SERVICE_CALL_FAILED,
        );
      }
      this.logger.info(Messages.GRPC_CALL_SUCCESS(opts.serviceName, opts.path));
      return result;
    } catch (error) {
      const code = (error as grpc.ServiceError).code;
      if (code === grpc.status.UNAVAILABLE || code === grpc.status.DEADLINE_EXCEEDED) {
        this.logger.warning(Messages.GRPC_CALL_FALLBACK(opts.serviceName, opts.path));
        return null;
      }
      throw error;
    } finally {
      client.close();
    }
  }

  private springGrpcRoute(method: Method, path: string): { path: string } | null {
    if (optsMethodIsGet(method) && /^\/articles\/[^/]+$/.test(path)) {
      return { path: "/spring.v1.Article/Get" };
    }
    if (method === "POST" && path === "/articles/batch") {
      return { path: "/spring.v1.Article/Batch" };
    }
    if (optsMethodIsGet(method) && path === "/articles/by-title") {
      return { path: "/spring.v1.Article/ByTitle" };
    }
    if (optsMethodIsGet(method) && /^\/users\/[0-9]+$/.test(path)) {
      return { path: UserService.get.path };
    }
    if (method === "POST" && path === "/users/batch") return { path: UserService.batch.path };
    if (optsMethodIsGet(method) && path === "/users/by-name") return { path: UserService.byName.path };
    if (optsMethodIsGet(method) && /^\/users\/by-github-id\/.+/.test(path)) {
      return { path: UserService.byGithubId.path };
    }
    if (method === "POST" && path === "/users/github-user") return { path: UserService.githubUser.path };
    if (optsMethodIsGet(method) && /^\/users\/[0-9]+\/is-admin$/.test(path)) {
      return { path: UserService.isAdmin.path };
    }
    if (method === "POST" && path === "/users/github/token-ticket") {
      return { path: UserService.tokenTicket.path };
    }
    return null;
  }
}

function optsMethodIsGet(method: Method): boolean {
  return method.toUpperCase() === "GET";
}
