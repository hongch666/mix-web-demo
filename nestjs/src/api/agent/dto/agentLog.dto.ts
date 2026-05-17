import { ApiProperty } from '@nestjs/swagger';
import {
  IsIn,
  IsInt,
  IsObject,
  IsOptional,
  Max,
  Min,
} from 'class-validator';
import { Constants } from 'src/common/utils/constants';

export class AgentLogQueryDto {
  @ApiProperty({
    description: Constants.AGENT_LOG_COLLECTION_DESC,
    enum: ['apilogs', 'articlelogs'],
  })
  @IsIn(['apilogs', 'articlelogs'])
  collection!: 'apilogs' | 'articlelogs';

  @ApiProperty({ description: Constants.AGENT_LOG_FILTER_DESC, required: false })
  @IsOptional()
  @IsObject()
  filter?: Record<string, unknown>;

  @ApiProperty({
    description: Constants.AGENT_LOG_LIMIT_DESC,
    default: 10,
    maximum: 100,
  })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number;

  @ApiProperty({ description: Constants.AGENT_LOG_SORT_DESC, required: false })
  @IsOptional()
  @IsObject()
  sort?: Record<string, 1 | -1>;
}
