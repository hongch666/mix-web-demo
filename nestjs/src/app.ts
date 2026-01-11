import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { DocumentBuilder, OpenAPIObject, SwaggerModule } from '@nestjs/swagger';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import { ResponseInterceptor } from './common/interceptors/response.interceptor';
import { AllExceptionsFilter } from './common/filters/all-exception.filter';

export async function createApp(): Promise<INestApplication> {
  const app: INestApplication<any> = await NestFactory.create(AppModule);

  // Swagger 配置
  const config: Omit<OpenAPIObject, 'paths'> = new DocumentBuilder()
    .setTitle('NestJS部分的Swagger文档集成')
    .setDescription('这是demo项目的NestJS部分的Swagger文档集成')
    .setVersion('1.0')
    .build();
  const document: OpenAPIObject = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api-docs', app, document);

  // 注册全局异常过滤器
  app.useGlobalFilters(new AllExceptionsFilter());
  //全局启用校验管道
  app.useGlobalPipes(new ValidationPipe({ transform: true }));
  // 全局注册拦截器
  app.useGlobalInterceptors(new ResponseInterceptor());
  // 返回 app
  return app;
}
