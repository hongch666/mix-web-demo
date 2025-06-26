import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ConfigService } from '@nestjs/config';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { ValidationPipe } from '@nestjs/common';
import { ResponseInterceptor } from './common/utils/response.interceptor';
import { AllExceptionsFilter } from './common/filters/all-exception.filter';

// TODO: 用户表修改，要修改实体类
// TODO: 终端日志保存到专门的日志文件中

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // Swagger 配置
  const config = new DocumentBuilder()
    .setTitle('NestJS部分的Swagger文档集成')
    .setDescription('这是demo项目的NestJS部分的Swagger文档集成')
    .setVersion('1.0')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api-docs', app, document);
  // 注册全局异常过滤器
  app.useGlobalFilters(new AllExceptionsFilter());
  //全局启用校验管道
  app.useGlobalPipes(new ValidationPipe({ transform: true }));
  // 全局注册拦截器
  app.useGlobalInterceptors(new ResponseInterceptor());

  // 读取yaml文件中的端口
  const configService = app.get(ConfigService);
  const port = configService.get<number>('server.port') || 3000;
  await app.listen(port);
}
bootstrap();
