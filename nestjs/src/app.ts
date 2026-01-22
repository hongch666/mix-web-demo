import { NestFactory } from '@nestjs/core';
import {
  FastifyAdapter,
  NestFastifyApplication,
} from '@nestjs/platform-fastify';
import { AppModule } from './app.module';
import { DocumentBuilder, OpenAPIObject, SwaggerModule } from '@nestjs/swagger';
import { ValidationPipe } from '@nestjs/common';
import { AllExceptionsFilter } from './common/filters/all-exception.filter';
import { Constants } from './common/utils/constants';

export async function createApp(): Promise<NestFastifyApplication> {
  const app: NestFastifyApplication =
    await NestFactory.create<NestFastifyApplication>(
      AppModule,
      new FastifyAdapter(),
    );

  // Swagger 配置
  const config: Omit<OpenAPIObject, 'paths'> = new DocumentBuilder()
    .setTitle(Constants.SWAGGER_TITLE)
    .setDescription(Constants.SWAGGER_DESCRIPTION)
    .setVersion(Constants.SWAGGER_VERSION)
    .build();
  const document: OpenAPIObject = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup(Constants.SWAGGER_PATH, app, document);

  // 注册全局异常过滤器
  app.useGlobalFilters(new AllExceptionsFilter());
  //全局启用校验管道
  app.useGlobalPipes(new ValidationPipe({ transform: true }));
  // 返回 app
  return app;
}
