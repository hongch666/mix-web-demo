import { Global, Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { RabbitMQModule } from '@golevelup/nestjs-rabbitmq';

@Global()
@Module({
  imports: [
    RabbitMQModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => {
        const host: string = configService.get<string>('rabbitmq.host')!;
        const port: number = configService.get<number>('rabbitmq.port')!;
        const username: string = configService.get<string>('rabbitmq.username')!;
        const password: string = configService.get<string>('rabbitmq.password')!;
        const vhost: string = configService.get<string>('rabbitmq.vhost')!;
        const uri: string = `amqp://${username}:${password}@${host}:${port}${vhost === '/' ? '' : `/${vhost}`}`;

        return {
          uri,
          exchanges: [],
          defaultRpcTimeout: 10000,
          defaultExchangeType: 'direct',
          connectionInitOptions: { timeout: 10000 },
          queues: [
            {
              name: 'api-log-queue',
              options: { durable: true },
            },
            {
              name: 'article-log-queue',
              options: { durable: true },
            },
          ],
        };
      },
    }),
  ],
  exports: [RabbitMQModule],
})
export class AppRabbitMQModule {}
