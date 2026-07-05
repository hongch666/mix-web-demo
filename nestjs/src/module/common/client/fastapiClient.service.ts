import { Injectable } from '@nestjs/common';
import { NacosService } from '../nacos/nacos.service';

@Injectable()
export class FastapiClientService {
  constructor(private readonly nacosService: NacosService) {}

  async test(): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'fastapi',
      method: 'GET',
      path: '/api_fastapi/fastapi',
    });
  }
}
