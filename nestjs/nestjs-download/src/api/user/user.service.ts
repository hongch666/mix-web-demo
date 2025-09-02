import { Injectable } from '@nestjs/common';
import { NacosService } from 'src/common/nacos/nacos.service';

@Injectable()
export class UserService {
  constructor(private readonly nacosService: NacosService) {}

  // 查询用户
  async getUserById(id: number): Promise<any> {
    // 使用Spring进行远程调用
    const res = await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: `/users/:id`,
      pathParams: { id: id.toString() },
    });

    return res.data;
  }
}
