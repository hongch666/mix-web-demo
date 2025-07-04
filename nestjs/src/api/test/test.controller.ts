import { Controller, Get } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ClsService } from 'nestjs-cls';
import { NacosService } from 'src/common/nacos/nacos.service';
import { fileLogger } from 'src/common/utils/writeLog';

@Controller('api_nestjs')
@ApiTags('测试模块')
export class TestController {
  constructor(
    private readonly nacosService: NacosService,
    private readonly cls: ClsService,
  ) {}

  @Get('nestjs')
  @ApiOperation({ summary: 'NestJS自己的测试', description: '输出欢迎信息' })
  async getNestjs(): Promise<any> {
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' +
        userId +
        ':' +
        username +
        ' GET /api_nestjs/nestjs: 测试NestJS服务',
    );
    return 'Hello,I am Nest.js!';
  }

  @Get('spring')
  @ApiOperation({ summary: '调用Spring的测试', description: '输出欢迎信息' })
  async getSpring(): Promise<any> {
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' +
        userId +
        ':' +
        username +
        ' GET /api_nestjs/spring: 测试Spring服务',
    );
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
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' + userId + ':' + username + ' GET /api_nestjs/gin: 测试Gin服务',
    );
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
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' +
        userId +
        ':' +
        username +
        ' GET /api_nestjs/fastapi: 测试FastAPI服务',
    );
    const res = await this.nacosService.call({
      serviceName: 'fastapi',
      method: 'GET',
      path: '/api_fastapi/fastapi',
    });
    return res.data;
  }
}
