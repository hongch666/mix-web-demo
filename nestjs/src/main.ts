import { createApp } from './app';
import { ConfigService } from '@nestjs/config';
import { NestFastifyApplication } from '@nestjs/platform-fastify';

async function bootstrap(): Promise<void> {
  const app: NestFastifyApplication = await createApp();
  // 读取yaml文件中的端口和IP
  const configService: ConfigService<unknown, boolean> = app.get(ConfigService);
  const port: number = configService.get<number>('server.port') || 3000;
  const ip: string = configService.get<string>('server.ip') || '127.0.0.1';
  // 监听服务端口
  await app.listen(port, ip);
}

bootstrap();
