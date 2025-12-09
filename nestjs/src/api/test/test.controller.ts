import { Controller, Get } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ClsService } from 'nestjs-cls';
import { ApiLog } from 'src/common/decorators/api-log.decorator';
import { NacosService } from 'src/modules/nacos/nacos.service';

@Controller('api_nestjs')
@ApiTags('测试模块')
export class TestController {
  constructor(
    private readonly nacosService: NacosService,
    private readonly cls: ClsService,
  ) {}

  @Get('nestjs')
  @ApiOperation({ summary: 'NestJS自己的测试', description: '输出欢迎信息' })
  @ApiLog('测试NestJS服务')
  async getNestjs(): Promise<any> {
    return 'Hello,I am Nest.js!';
  }

  @Get('spring')
  @ApiOperation({ summary: '调用Spring的测试', description: '输出欢迎信息' })
  @ApiLog('测试Spring服务')
  async getSpring(): Promise<any> {
    const res = await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/api_spring/spring',
    });
    return res.data;
  }

  @Get('gin')
  @ApiOperation({ summary: '调用Gin的测试', description: '输出欢迎信息' })
  @ApiLog('测试Gin服务')
  async getGin(): Promise<any> {
    const res = await this.nacosService.call({
      serviceName: 'gin',
      method: 'GET',
      path: '/api_gin/gin',
    });
    return res.data;
  }

  @Get('fastapi')
  @ApiOperation({ summary: '调用FastAPI的测试', description: '输出欢迎信息' })
  @ApiLog('测试FastAPI服务')
  async getFastAPI(): Promise<any> {
    const res = await this.nacosService.call({
      serviceName: 'fastapi',
      method: 'GET',
      path: '/api_fastapi/fastapi',
    });
    return res.data;
  }
}
