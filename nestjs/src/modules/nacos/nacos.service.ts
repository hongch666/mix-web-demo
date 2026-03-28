import { Injectable, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios, { Method } from 'axios';
import { NacosNamingClient } from 'nacos';
import { ClsService } from 'nestjs-cls';
import * as os from 'os';
import qs from 'qs';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import { InternalTokenUtil } from 'src/common/utils/internalToken.util';
import { logger } from '../../common/utils/writeLog';

interface CallOptions {
  serviceName: string;
  method: Method; // 'GET' | 'POST' | 'PUT' | 'DELETE'
  path: string;
  pathParams?: Record<string, string>;
  queryParams?: Record<string, string>;
  body?: Record<string, unknown>;
  headers?: Record<string, string>;
}

@Injectable()
export class NacosService implements OnModuleInit {
  private client!: NacosNamingClient;

  constructor(
    private readonly configService: ConfigService,
    private readonly cls: ClsService,
    private readonly internalTokenUtil: InternalTokenUtil,
  ) {}

  async onModuleInit(): Promise<void> {
    // 取消终端与nacos相关的日志,如果需要日志可以将下面的logger设置为console
    const silentLogger: Record<string, (message?: unknown) => void> =
      Object.create(console);
    silentLogger.log = (): void => {};
    silentLogger.info = (): void => {};
    silentLogger.debug = (): void => {};
    silentLogger.warn = (): void => {};

    const nacosHost: string =
      this.configService.get<string>('nacos.host') || '127.0.0.1';
    const nacosPort: string =
      this.configService.get<string>('nacos.port') || '8848';
    const nacosServerList: string = this.resolveNacosServerList(
      nacosHost,
      nacosPort,
    );

    this.client = new NacosNamingClient({
      logger: silentLogger,
      // Nacos 服务地址，默认端口为 8848
      serverList: nacosServerList,
      // 命名空间 ID
      namespace: this.configService.get<string>('nacos.namespace')!,
    });

    await this.client.ready();

    // 获取注册的 IP 地址，处理本地地址
    let registrationIp = this.configService.get<string>('server.ip')!;
    if (
      !registrationIp ||
      registrationIp === '127.0.0.1' ||
      registrationIp === '0.0.0.0'
    ) {
      // 自动解析
      registrationIp = this.getLocalIp();
      logger.info(`本地 IP 已转换为: ${registrationIp}`);
    }

    // 注册当前服务
    await this.client.registerInstance(
      this.configService.get<string>('server.serviceName')!,
      {
        ip: registrationIp,
        port: this.configService.get<string>('server.port')!,
        weight: 1,
        ephemeral: true,
        clusterName: this.configService.get<string>('nacos.clusterName')!,
        serviceName: this.configService.get<string>('server.serviceName')!,
        enabled: true,
        healthy: true,
        metadata: {
          version: '1.0.0',
        },
      } as any,
    );

    logger.info(Constants.REGISTER_NACOS);
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
        if (addr.family === 'IPv4' && !addr.internal) {
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
    const trimmedPort = port.trim() || '8848';

    if (trimmedHost.includes(':') && !trimmedHost.startsWith('[')) {
      return trimmedHost;
    }

    return `${trimmedHost}:${trimmedPort}`;
  }

  async getServiceInstances(
    serviceName: string,
  ): Promise<Record<string, unknown>[]> {
    const instances: Record<string, unknown>[] =
      (await this.client.getAllInstances(serviceName)) as Record<
        string,
        unknown
      >[];
    return instances;
  }

  async call(opts: CallOptions): Promise<Record<string, unknown>> {
    const instances: Record<string, unknown>[] = await this.getServiceInstances(
      opts.serviceName,
    );
    if (!instances || instances.length === 0) {
      throw new BusinessException(`服务 ${opts.serviceName} 无可用实例`);
    }

    // 负载均衡策略：随机
    const instance: Record<string, unknown> =
      instances[Math.floor(Math.random() * instances.length)]!;

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
      : '';
    const url: string = `http://${instance.ip as string}:${instance.port as number}${path}${queryString}`;

    // 默认请求头
    const userId: string = this.cls.get<string>('userId') || '0';
    const userName: string =
      this.cls.get<string>('username') || Constants.UNKNOWN_USER;
    const defaultHeaders: Record<string, string> = {
      'X-User-Id': userId,
      'X-Username': userName,
    };

    // 生成并添加内部服务令牌 (没有用户ID时用-1代表系统调用)
    const userIdNum: number = parseInt(userId, 10) || -1;
    const finalUserId: number = userIdNum > 0 ? userIdNum : -1;
    const internalToken: string =
      await this.internalTokenUtil.generateInternalToken(
        finalUserId,
        this.configService.get<string>('server.serviceName')!,
      );
    defaultHeaders['X-Internal-Token'] = `Bearer ${internalToken}`;

    // 合并默认请求头和自定义请求头
    const headers: Record<string, string> = {
      ...defaultHeaders,
      ...(opts.headers || {}),
    };

    // 请求配置
    const response: { data: Record<string, unknown> } = await axios.request({
      url,
      method: opts.method,
      data: opts.body,
      headers,
      timeout: 10000,
    });

    return response.data;
  }
}
