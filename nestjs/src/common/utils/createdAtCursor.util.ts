import { Types } from "mongoose";

/** 按 createdAt 倒序翻页的游标，时间戳与 _id 联合定位唯一一条记录 */
export interface CreatedAtCursor {
  /** 游标记录的创建时间 */
  createdAt: Date;
  /** 游标记录的 MongoDB 主键，用于同一毫秒内的次序判定 */
  id: Types.ObjectId;
}

/** 游标中时间戳与 _id 的分隔符，_id 本身不含下划线 */
const CURSOR_SEPARATOR = "_";

/** 游标格式：毫秒时间戳 + 分隔符 + 24 位 ObjectId */
const CURSOR_PATTERN = /^(\d{1,15})_([0-9a-fA-F]{24})$/;

/** createdAt 倒序翻页的排序键，_id 作为同一毫秒内的次序补充 */
export const CREATED_AT_DESC_SORT: Record<string, -1> = {
  createdAt: -1,
  _id: -1,
};

/**
 * 把列表最后一条记录编码为下一页游标
 */
export function encodeCreatedAtCursor(
  createdAt: Date,
  id: Types.ObjectId,
): string {
  return `${createdAt.getTime()}${CURSOR_SEPARATOR}${String(id)}`;
}

/**
 * 解析游标，格式非法时返回 null 由调用方退化为首页查询
 */
export function parseCreatedAtCursor(cursor?: string): CreatedAtCursor | null {
  if (!cursor) {
    return null;
  }

  const matched: RegExpExecArray | null = CURSOR_PATTERN.exec(cursor.trim());
  if (!matched) {
    return null;
  }

  const createdAt: Date = new Date(Number(matched[1]));
  if (Number.isNaN(createdAt.getTime())) {
    return null;
  }

  return { createdAt, id: new Types.ObjectId(matched[2]!) };
}

/**
 * 构造 createdAt + _id 的 seek 条件，配合 createdAt_-1__id_-1 索引避免深分页 skip 扫描
 */
export function buildCreatedAtSeekFilter(
  cursor: CreatedAtCursor,
): Record<string, unknown> {
  return {
    $or: [
      { createdAt: { $lt: cursor.createdAt } },
      { createdAt: cursor.createdAt, _id: { $lt: cursor.id } },
    ],
  };
}
