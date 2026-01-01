import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, DeleteResult } from 'mongoose';
import { ApiLog, ApiLogDocument } from './schema/api-log.schema';
import { CreateApiLogDto, QueryApiLogDto } from './dto/api-log.dto';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import isLeapYear from 'dayjs/plugin/isLeapYear';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(isLeapYear);

const TIMEZONE = 'Asia/Shanghai';

@Injectable()
export class ApiLogService {
  constructor(
    @InjectModel(ApiLog.name)
    private readonly apiLogModel: Model<ApiLogDocument>,
  ) {}

  /**
   * 创建API日志
   * @param dto 创建日志DTO
   */
  async create(dto: CreateApiLogDto) {
    return this.apiLogModel.create(dto);
  }

  /**
   * 根据ID删除日志
   * @param id 日志ID
   */
  async removeById(id: string) {
    return this.apiLogModel.findByIdAndDelete(id).exec();
  }

  /**
   * 批量删除日志
   * @param ids 日志ID数组
   */
  async removeByIds(ids: string[]): Promise<DeleteResult> {
    return this.apiLogModel.deleteMany({ _id: { $in: ids } }).exec();
  }

  /**
   * 根据条件查询日志（分页）
   * @param query 查询条件
   */
  async findByFilter(query: QueryApiLogDto) {
    const {
      userId,
      username,
      apiDescription,
      apiPath,
      apiMethod,
      startTime,
      endTime,
      page = '1',
      size = '10',
    } = query;

    const filters: Record<string, any> = {};

    if (userId) filters.userId = Number(userId);
    if (username) filters.username = { $regex: username, $options: 'i' };
    if (apiDescription)
      filters.apiDescription = { $regex: apiDescription, $options: 'i' };
    if (apiPath) filters.apiPath = { $regex: apiPath, $options: 'i' };
    if (apiMethod) filters.apiMethod = apiMethod;

    if (startTime || endTime) {
      filters.createdAt = {};
      if (startTime)
        filters.createdAt.$gte = dayjs(
          startTime,
          'YYYY-MM-DD HH:mm:ss',
        ).toDate();
      if (endTime)
        filters.createdAt.$lte = dayjs(endTime, 'YYYY-MM-DD HH:mm:ss').toDate();
    }

    const skip = (parseInt(page) - 1) * parseInt(size);
    const take = parseInt(size);

    const [total, list] = await Promise.all([
      this.apiLogModel.countDocuments(filters),
      this.apiLogModel
        .find(filters)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(take)
        .exec(),
    ]);

    // 格式化返回数据
    const resultList = list.map((log) => ({
      _id: log._id,
      userId: log.userId,
      username: log.username,
      apiDescription: log.apiDescription,
      apiPath: log.apiPath,
      apiMethod: log.apiMethod,
      queryParams: log.queryParams,
      pathParams: log.pathParams,
      requestBody: log.requestBody,
      responseTime: log.responseTime,
      createdAt: log.createdAt
        ? dayjs(log.createdAt).tz(TIMEZONE).format('YYYY-MM-DD HH:mm:ss')
        : undefined,
      updatedAt: log.updatedAt
        ? dayjs(log.updatedAt).tz(TIMEZONE).format('YYYY-MM-DD HH:mm:ss')
        : undefined,
    }));

    return { total, list: resultList };
  }
}
