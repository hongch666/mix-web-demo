import { Module } from '@nestjs/common';
import { AgentController } from './agent.controller';
import { AgentService } from './agent.service';

@Module({
  providers: [AgentService],
  controllers: [AgentController],
})
export class AgentModule {}
