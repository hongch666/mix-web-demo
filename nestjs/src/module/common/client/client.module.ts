import { Module } from '@nestjs/common';
import { NacosModule } from '../nacos/nacos.module';
import { FastapiClientService } from './fastapiClient.service';
import { GoZeroClientService } from './gozeroClient.service';
import { SpringClientService } from './springClient.service';

@Module({
  imports: [NacosModule],
  providers: [FastapiClientService, GoZeroClientService, SpringClientService],
  exports: [FastapiClientService, GoZeroClientService, SpringClientService],
})
export class ClientModule {}
