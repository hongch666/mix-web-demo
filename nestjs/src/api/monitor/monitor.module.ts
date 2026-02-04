import { Module, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { MonitorController } from './monitor.controller';
import { MonitorService } from './monitor.service';

@Module({
  providers: [MonitorService],
  controllers: [MonitorController],
  exports: [MonitorService],
})
export class MonitorModule implements OnModuleInit, OnModuleDestroy {
  constructor(private monitorService: MonitorService) {}

  onModuleInit(): void {
    this.monitorService.startMonitoring();
  }

  onModuleDestroy(): void {
    this.monitorService.stopMonitoring();
  }
}
