import { Body, Controller, Delete, Get, Param, Put } from "@nestjs/common";
import { ApiBody, ApiOperation, ApiParam, ApiTags } from "@nestjs/swagger";
import {
  ApiResponseModel,
  SwaggerNullData,
  SwaggerTableSettingsData,
  SwaggerTableSettingsListData,
} from "src/common/utils/swaggerResponse";
import { ClsService } from "nestjs-cls";
import { ErrorIds, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { ApiResponse, success } from "src/common/utils/response";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
import { SaveTableSettingsDto } from "./dto/tableSettings.dto";
import { TableSettings } from "./entities/tableSettings.entity";
import { TableSettingsService } from "./tableSettings.service";

@Controller("table-settings")
@ApiTags("表格列设置")
export class TableSettingsController {
  constructor(
    private readonly tableSettingsService: TableSettingsService,
    private readonly cls: ClsService,
  ) {}

  @Get("")
  @ApiOperation({
    summary: "获取当前用户所有页面的列配置",
    description: "返回当前登录用户所有已保存的表格列设置",
  })
  @ApiLog("获取所有列配置")
  @ApiResponseModel({ data: SwaggerTableSettingsListData })
  async getAllSettings(): Promise<ApiResponse<TableSettings[]>> {
    const userId: number = this.cls.get<number>("userId");
    if (!userId) {
      throw BusinessException.unauthorized(
        Messages.UNAUTHORIZED_USER,
        ErrorIds.UNAUTHORIZED_USER_ERROR,
      );
    }
    const settings: TableSettings[] =
      await this.tableSettingsService.getAllSettings(userId);
    return success(settings);
  }

  @Get(":table_key")
  @ApiOperation({
    summary: "获取指定页面的列配置",
    description: "获取当前登录用户在指定页面的表格列设置",
  })
  @ApiParam({ name: "table_key", type: "string", description: "页面标识" })
  @ApiLog("获取列配置")
  @ApiResponseModel({ data: SwaggerTableSettingsData })
  async getSettings(
    @Param("table_key") tableKey: string,
  ): Promise<ApiResponse<TableSettings | null>> {
    const userId: number = this.cls.get<number>("userId");
    if (!userId) {
      throw BusinessException.unauthorized(
        Messages.UNAUTHORIZED_USER,
        ErrorIds.UNAUTHORIZED_USER_ERROR,
      );
    }
    const settings: TableSettings | null =
      await this.tableSettingsService.getSettings(userId, tableKey);
    return success(settings);
  }

  @Put(":table_key")
  @ApiOperation({
    summary: "保存指定页面的列配置",
    description: "保存（新增或更新）当前登录用户在指定页面的表格列设置",
  })
  @ApiParam({ name: "table_key", type: "string", description: "页面标识" })
  @ApiBody({ type: SaveTableSettingsDto })
  @ApiLog("保存列配置")
  @ApiResponseModel({ data: SwaggerNullData })
  async saveSettings(
    @Param("table_key") tableKey: string,
    @Body() dto: SaveTableSettingsDto,
  ): Promise<ApiResponse<null>> {
    const userId: number = this.cls.get<number>("userId");
    if (!userId) {
      throw BusinessException.unauthorized(
        Messages.UNAUTHORIZED_USER,
        ErrorIds.UNAUTHORIZED_USER_ERROR,
      );
    }
    await this.tableSettingsService.saveSettings(userId, tableKey, dto.columns);
    return success(null);
  }

  @Delete(":table_key")
  @ApiOperation({
    summary: "删除指定页面的列配置",
    description: "删除当前登录用户在指定页面的表格列设置，恢复为默认配置",
  })
  @ApiParam({ name: "table_key", type: "string", description: "页面标识" })
  @ApiLog("删除列配置")
  @ApiResponseModel({ data: SwaggerNullData })
  async deleteSettings(
    @Param("table_key") tableKey: string,
  ): Promise<ApiResponse<null>> {
    const userId: number = this.cls.get<number>("userId");
    if (!userId) {
      throw BusinessException.unauthorized(
        Messages.UNAUTHORIZED_USER,
        ErrorIds.UNAUTHORIZED_USER_ERROR,
      );
    }
    await this.tableSettingsService.deleteSettings(userId, tableKey);
    return success(null);
  }
}
