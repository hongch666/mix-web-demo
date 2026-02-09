import { NestFactory } from '@nestjs/core';
import {
  FastifyAdapter,
  NestFastifyApplication,
} from '@nestjs/platform-fastify';
import { DocumentBuilder, OpenAPIObject, SwaggerModule } from '@nestjs/swagger';
import { Logger, ValidationPipe } from '@nestjs/common';
import { AllExceptionsFilter } from '../common/filters/all-exception.filter';
import { Constants } from '../common/utils/constants';
import { ConfigService } from '@nestjs/config';
import { AppModule } from './app.module';

export async function createApp(): Promise<NestFastifyApplication> {
  const fastifyAdapter: FastifyAdapter = new FastifyAdapter();

  const app: NestFastifyApplication =
    await NestFactory.create<NestFastifyApplication>(AppModule, fastifyAdapter);

  // 配置 Fastify 以接受没有 Content-Type 的请求（解决 DELETE 请求的 Unsupported Media Type 错误）
  const fastifyInstance = app.getHttpAdapter().getInstance();
  // 使用安全的正则表达式来处理各种 Content-Type
  fastifyInstance.addContentTypeParser(
    /^.*/,
    async (_req: unknown, payload: NodeJS.ReadableStream): Promise<unknown> => {
      return payload;
    },
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
  // 读取yaml文件中的端口和IP
  const configService: ConfigService<unknown, boolean> = app.get(ConfigService);
  const port: number = configService.get<number>('server.port')!;
  const ip: string = configService.get<string>('server.ip')!;
  // 输出启动信息和Swagger地址
  Logger.log(Constants.START_WELCOME);
  Logger.log(`服务地址: http://${ip}:${port}`);
  Logger.log(`Swagger文档地址: http://${ip}:${port}/api-docs`);
  // 返回 app
  return app;
}
