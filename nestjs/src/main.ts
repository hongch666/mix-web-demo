import { ConfigService } from '@nestjs/config';
import { NestFastifyApplication } from '@nestjs/platform-fastify';
import { createApp } from './app';

async function bootstrap(): Promise<void> {
  // 初始化app
  const app: NestFastifyApplication = await createApp();
  // 获取 NestJS 服务的端口和IP
  const configService: ConfigService<unknown, boolean> = app.get(ConfigService);
  const port: number = configService.get<number>('server.port')!;
  const ip: string = configService.get<string>('server.ip')!;
  // 监听服务
  await app.listen(port, ip);
}

bootstrap();
