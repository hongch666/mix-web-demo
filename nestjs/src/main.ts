import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { AllExceptionsFilter } from './filters/all-exception.filter';
import { ConfigService } from '@nestjs/config';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // 注册全局异常过滤器
  app.useGlobalFilters(new AllExceptionsFilter());
  //读取yaml文件中的端口
  const configService = app.get(ConfigService);
  const port = configService.get<number>('server.port') || 3000;
  await app.listen(port);
}
bootstrap();
