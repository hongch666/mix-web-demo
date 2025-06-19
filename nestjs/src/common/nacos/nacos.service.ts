import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { NacosNamingClient } from 'nacos';
import { ConfigService } from '@nestjs/config';
import axios, { Method } from 'axios';
import qs from 'qs';
import { ClsService } from 'nestjs-cls';

interface CallOptions {
  serviceName: string;
  method: Method; // 'GET' | 'POST' | 'PUT' | 'DELETE'
  path: string;
  pathParams?: Record<string, string>;
  queryParams?: Record<string, string>;
  body?: any;
  headers?: Record<string, string>;
}

@Injectable()
export class NacosService implements OnModuleInit {
  private client: NacosNamingClient;

  constructor(
    private readonly configService: ConfigService,
    private readonly cls: ClsService,
  ) {}

  async onModuleInit() {
    // 取消终端与nacos相关的日志,如果需要日志可以将下面的logger设置为console
    const silentLogger = Object.create(console);
    silentLogger.log = () => {};
    silentLogger.info = () => {};
    silentLogger.debug = () => {};
    silentLogger.warn = () => {};

    this.client = new NacosNamingClient({
      logger: silentLogger,
      // Nacos 服务地址
      serverList:
        this.configService.get<string>('nacos.server-addr') || '127.0.0.1:8848',
      // 命名空间 ID
      namespace: this.configService.get<string>('nacos.namespace') || 'public',
    });

    await this.client.ready();

    // 注册当前服务
    await this.client.registerInstance(
      this.configService.get<string>('server.serviceName') || 'nestjs',
      {
        ip: this.configService.get<string>('server.ip') || '127.0.0.1',
        port: this.configService.get<string>('server.port') || 3000,
        weight: 1,
        ephemeral: true,
        clusterName:
          this.configService.get<string>('nacos.clusterName') || 'DEFAULT',
        serviceName:
          this.configService.get<string>('server.serviceName') || 'nestjs',
        enabled: true,
        healthy: true,
        metadata: {
          version: '1.0.0',
        },
      } as any,
    );

    Logger.log('注册到 nacos 成功');
  }

  async getServiceInstances(serviceName: string) {
    const instances = await this.client.getAllInstances(serviceName);
    return instances;
  }

  async call(opts: CallOptions): Promise<any> {
    const instances = await this.getServiceInstances(opts.serviceName);
    if (!instances || instances.length === 0) {
      throw new Error(`服务 ${opts.serviceName} 无可用实例`);
    }

    // 负载均衡策略：随机
    const instance = instances[Math.floor(Math.random() * instances.length)];

    // 替换 pathParams
    let path = opts.path;
    if (opts.pathParams) {
      for (const [key, value] of Object.entries(opts.pathParams)) {
        path = path.replace(`:${key}`, value);
      }
    }

    // 拼接 URL
    const queryString = opts.queryParams
      ? `?${qs.stringify(opts.queryParams)}`
      : '';
    const url = `http://${instance.ip}:${instance.port}${path}${queryString}`;

    // 默认请求头
    const userId = this.cls.get('userId') || ' ';
    const userName = this.cls.get('username') || ' ';
    const defaultHeaders = {
      'X-User-Id': userId,
      'X-Username': userName,
    };

    // 合并默认请求头和自定义请求头
    const headers = {
      ...defaultHeaders,
      ...(opts.headers || {}),
    };

    // 请求配置
    const response = await axios.request({
      url,
      method: opts.method,
      data: opts.body,
      headers,
      timeout: 10000,
    });

    return response.data;
  }
}
