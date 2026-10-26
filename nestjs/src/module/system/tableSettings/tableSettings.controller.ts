import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Put,
  Query,
} from "@nestjs/common";
import {
  ApiBody,
  ApiOperation,
  ApiParam,
  ApiQuery,
  ApiTags,
} from "@nestjs/swagger";
import { ClsService } from "nestjs-cls";
import { ErrorIds, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import {
  ApiResponseModel,
  SwaggerNullData,
  SwaggerTableSettingsData,
  SwaggerTableSettingsListData,
} from "src/common/utils/swaggerResponse";
import { ApiResponse, success } from "src/common/utils/response";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
import { RequireSelf } from "src/framework/decorators/requireSelf.decorator";
import {
  SaveTableSettingsDto,
  TableSettingsQueryDto,
} from "./dto/tableSettings.dto";
import { TableSettings } from "./entities/tableSettings.entity";
import { TableSettingsService } from "./tableSettings.service";

/**
 * 表格列设置接口，提供用户各页面列配置的查询、保存与删除
 * 缺省操作当前登录用户的数据，指定 user_id 时要求本人或管理员
 */
@Controller("table-settings")
@ApiTags("表格列设置")
export class TableSettingsController {
  constructor(
    private readonly tableSettingsService: TableSettingsService,
    private readonly cls: ClsService,
  ) {}

  /**
   * 获取目标用户所有页面的表格列配置
   */
  @Get("")
  @ApiOperation({
    summary: "获取指定用户所有页面的列配置",
    description: "返回目标用户所有已保存的表格列设置，缺省为当前登录用户",
  })
  @ApiQuery({
    name: "user_id",
    type: Number,
    required: false,
    description: "目标用户ID，缺省为当前登录用户，指定他人时需要管理员权限",
  })
  @RequireSelf()
  @ApiLog("获取所有列配置")
  @ApiResponseModel({ data: SwaggerTableSettingsListData })
  async getAllSettings(
    @Query() query: TableSettingsQueryDto,
  ): Promise<ApiResponse<TableSettings[]>> {
    const settings: TableSettings[] =
      await this.tableSettingsService.getAllSettings(this.resolveUserId(query));
    return success(settings);
  }

  /**
   * 获取目标用户在指定页面的表格列配置
   */
  @Get(":table_key")
  @ApiOperation({
    summary: "获取指定页面的列配置",
    description: "获取目标用户在指定页面的表格列设置，缺省为当前登录用户",
  })
  @ApiParam({ name: "table_key", type: "string", description: "页面标识" })
  @ApiQuery({
    name: "user_id",
    type: Number,
    required: false,
    description: "目标用户ID，缺省为当前登录用户，指定他人时需要管理员权限",
  })
  @RequireSelf()
  @ApiLog("获取列配置")
  @ApiResponseModel({ data: SwaggerTableSettingsData })
  async getSettings(
    @Param("table_key") tableKey: string,
    @Query() query: TableSettingsQueryDto,
  ): Promise<ApiResponse<TableSettings | null>> {
    const settings: TableSettings | null =
      await this.tableSettingsService.getSettings(
        this.resolveUserId(query),
        tableKey,
      );
    return success(settings);
  }

  /**
   * 保存（新增或更新）目标用户在指定页面的表格列配置
   */
  @Put(":table_key")
  @ApiOperation({
    summary: "保存指定页面的列配置",
    description:
      "保存（新增或更新）目标用户在指定页面的表格列设置，缺省为当前登录用户",
  })
  @ApiParam({ name: "table_key", type: "string", description: "页面标识" })
  @ApiQuery({
    name: "user_id",
    type: Number,
    required: false,
    description: "目标用户ID，缺省为当前登录用户，指定他人时需要管理员权限",
  })
  @ApiBody({ type: SaveTableSettingsDto })
  @RequireSelf()
  @ApiLog("保存列配置")
  @ApiResponseModel({ data: SwaggerNullData })
  async saveSettings(
    @Param("table_key") tableKey: string,
    @Body() dto: SaveTableSettingsDto,
    @Query() query: TableSettingsQueryDto,
  ): Promise<ApiResponse<null>> {
    await this.tableSettingsService.saveSettings(
      this.resolveUserId(query),
      tableKey,
      dto.columns,
    );
    return success(null);
  }

  /**
   * 删除目标用户在指定页面的表格列配置，使其恢复默认配置
   */
  @Delete(":table_key")
  @ApiOperation({
    summary: "删除指定页面的列配置",
    description:
      "删除目标用户在指定页面的表格列设置并恢复默认，缺省为当前登录用户",
  })
  @ApiParam({ name: "table_key", type: "string", description: "页面标识" })
  @ApiQuery({
    name: "user_id",
    type: Number,
    required: false,
    description: "目标用户ID，缺省为当前登录用户，指定他人时需要管理员权限",
  })
  @RequireSelf()
  @ApiLog("删除列配置")
  @ApiResponseModel({ data: SwaggerNullData })
  async deleteSettings(
    @Param("table_key") tableKey: string,
    @Query() query: TableSettingsQueryDto,
  ): Promise<ApiResponse<null>> {
    await this.tableSettingsService.deleteSettings(
      this.resolveUserId(query),
      tableKey,
    );
    return success(null);
  }

  /**
   * 解析本次操作的目标用户，缺省回退为当前登录用户
   * 目标用户的本人或管理员校验由 @RequireSelf 对应的守卫完成
   */
  private resolveUserId(query: TableSettingsQueryDto): number {
    const currentUserId: number | undefined = this.cls.get<number>("userId");
    if (!currentUserId) {
      throw BusinessException.unauthorized(
        Messages.UNAUTHORIZED_USER,
        ErrorIds.UNAUTHORIZED_USER_ERROR,
      );
    }
    return query.user_id ?? currentUserId;
  }
}
