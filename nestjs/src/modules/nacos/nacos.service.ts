import { Injectable, OnModuleInit } from '@nestjs/common';
import { NacosNamingClient } from 'nacos';
import { ConfigService } from '@nestjs/config';
import axios, { Method } from 'axios';
import qs from 'qs';
import { ClsService } from 'nestjs-cls';
import { logger } from '../../common/utils/writeLog';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { InternalTokenUtil } from 'src/common/utils/internal-token.util';
import { Constants } from 'src/common/utils/constants';

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
    const silentLogger: Record<string, (message?: unknown) => void> = Object.create(console);
    silentLogger.log = (): void => {};
    silentLogger.info = (): void => {};
    silentLogger.debug = (): void => {};
    silentLogger.warn = (): void => {};

    this.client = new NacosNamingClient({
      logger: silentLogger,
      // Nacos 服务地址
      serverList: this.configService.get<string>('nacos.server-addr')!,
      // 命名空间 ID
      namespace: this.configService.get<string>('nacos.namespace')!,
    });

    await this.client.ready();

    // 注册当前服务
    await this.client.registerInstance(
      this.configService.get<string>('server.serviceName')!,
      {
        ip: this.configService.get<string>('server.ip')!,
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

  async getServiceInstances(serviceName: string): Promise<Record<string, unknown>[]> {
    const instances: Record<string, unknown>[] = (await this.client.getAllInstances(serviceName)) as Record<string, unknown>[];
    return instances;
  }

  async call(opts: CallOptions): Promise<Record<string, unknown>> {
    const instances: Record<string, unknown>[] = await this.getServiceInstances(opts.serviceName);
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
    const userName: string = this.cls.get<string>('username') || Constants.UNKNOWN_USER;
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
