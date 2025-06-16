import { Controller, Get, Logger } from '@nestjs/common';
import { NacosService } from '../nacos/nacos.service';
import { ApiOperation, ApiTags } from '@nestjs/swagger';

@Controller('api_nestjs')
@ApiTags('测试模块')
export class ClientController {
  constructor(private readonly nacosService: NacosService) {}

  @Get('nestjs')
  @ApiOperation({ summary: 'NestJS自己的测试', description: '输出欢迎信息' })
  async getNestjs(): Promise<any> {
    Logger.log('GET /api_nestjs/nestjs: 测试NestJS服务');
    return 'Hello,I am Nest.js!';
  }

  @Get('spring')
  @ApiOperation({ summary: '调用Spring的测试', description: '输出欢迎信息' })
  async getSpring(): Promise<any> {
    Logger.log('GET /api_nestjs/spring: 测试Spring服务');
    const res = await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/api_spring/spring',
    });
    return res.data;
  }

  @Get('gin')
  @ApiOperation({ summary: '调用Gin的测试', description: '输出欢迎信息' })
  async getGin(): Promise<any> {
    Logger.log('GET /api_nestjs/gin: 测试Gin服务');
    const res = await this.nacosService.call({
      serviceName: 'gin',
      method: 'GET',
      path: '/api_gin/gin',
    });
    return res.data;
  }

  @Get('fastapi')
  @ApiOperation({ summary: '调用FastAPI的测试', description: '输出欢迎信息' })
  async getFastAPI(): Promise<any> {
    Logger.log('GET /api_nestjs/fastapi: 测试FastAPI服务');
    const res = await this.nacosService.call({
      serviceName: 'fastapi',
      method: 'GET',
      path: '/api_fastapi/fastapi',
    });
    return res.data;
  }
}
