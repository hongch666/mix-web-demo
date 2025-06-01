import { Controller, Get, Post, Query, Param, Body, Req } from '@nestjs/common';
import { NacosService } from '../nacos/nacos.service';
import { success, error } from '../utils/response';
import { ApiOperation, ApiTags } from '@nestjs/swagger';

@Controller('api_nestjs')
@ApiTags('用户模块')
export class ClientController {
  constructor(private readonly nacosService: NacosService) {}

  @Get('nestjs')
  @ApiOperation({ summary: 'NestJS自己的测试', description: '输出欢迎信息' })
  async getNestjs(): Promise<any> {
    return success('Hello,I am Nest.js!');
  }

  @Get('spring')
  @ApiOperation({ summary: '调用Spring的测试', description: '输出欢迎信息' })
  async getSpring(): Promise<any> {
    return this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/api_spring/spring',
    });
  }

  @Get('gin')
  @ApiOperation({ summary: '调用Gin的测试', description: '输出欢迎信息' })
  async getGin(): Promise<any> {
    return this.nacosService.call({
      serviceName: 'gin',
      method: 'GET',
      path: '/api_gin/gin',
    });
  }
}
