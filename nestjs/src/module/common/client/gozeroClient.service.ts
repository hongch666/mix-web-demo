import { Injectable } from '@nestjs/common';
import { NacosService } from '../nacos/nacos.service';

@Injectable()
export class GoZeroClientService {
  constructor(private readonly nacosService: NacosService) {}

  async test(): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'gozero',
      method: 'GET',
      path: '/api_gozero/gozero',
    });
  }
}
