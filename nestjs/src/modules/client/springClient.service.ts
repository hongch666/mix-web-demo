import { Injectable } from '@nestjs/common';
import { NacosService } from 'src/modules/nacos/nacos.service';

@Injectable()
export class SpringClientService {
  constructor(private readonly nacosService: NacosService) {}

  async test(): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/api_spring/spring',
    });
  }

  async createTokenTicket(
    userId: number,
    username: string,
  ): Promise<Record<string, unknown>> {
    const safeUsername: string = username.replace(/[^\x20-\x7E]/g, '').trim();
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'POST',
      path: '/users/github/token-ticket',
      body: {
        user_id: userId,
        username,
      },
      headers: {
        'X-Username': safeUsername,
      },
    });
  }
}
