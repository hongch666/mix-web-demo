import { Body, Controller, Get, Post } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { Constants } from 'src/common/utils/constants';
import { ApiResponse, success } from 'src/common/utils/response';
import { RequireInternalToken } from 'src/framework/decorators/requireInternalToken.decorator';
import { AgentService } from './agent.service';
import { AgentLogQueryDto } from './dto/agentLog.dto';

@Controller('agent')
@ApiTags(Constants.AGENT_LOG_API_TAG)
export class AgentController {
  constructor(private readonly agentService: AgentService) {}

  @Get('log-collections')
  @ApiOperation({
    summary: Constants.AGENT_LOG_COLLECTIONS_SUMMARY,
    description: Constants.AGENT_LOG_COLLECTIONS_DESCRIPTION,
  })
  @RequireInternalToken()
  async listLogCollections(): Promise<ApiResponse<unknown>> {
    const data = await this.agentService.listLogCollections();
    return success(data);
  }

  @Post('log-query')
  @ApiOperation({
    summary: Constants.AGENT_LOG_QUERY_SUMMARY,
    description: Constants.AGENT_LOG_QUERY_DESCRIPTION,
  })
  @RequireInternalToken()
  async queryLog(
    @Body() dto: AgentLogQueryDto,
  ): Promise<ApiResponse<unknown>> {
    const data = await this.agentService.queryLog(dto);
    return success(data);
  }
}
