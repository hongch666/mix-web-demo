import { Injectable } from '@nestjs/common';
import { InjectConnection } from '@nestjs/mongoose';
import { Connection } from 'mongoose';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import { AgentLogQueryDto } from './dto/agentLog.dto';

interface LogCollectionInfo {
  name: string;
  document_count: number;
  sample_fields: string[];
}

@Injectable()
export class AgentService {
  private readonly allowedCollections = new Set(['apilogs', 'articlelogs']);

  private readonly blockedOperators = new Set([
    '$where',
    '$regex',
    '$function',
    '$accumulator',
  ]);

  constructor(@InjectConnection() private readonly connection: Connection) {}

  async listLogCollections(): Promise<{ collections: LogCollectionInfo[] }> {
    const collections: LogCollectionInfo[] = [];
    for (const collectionName of this.allowedCollections) {
      const collection = this.connection.collection(collectionName);
      const [documentCount, sampleDoc] = await Promise.all([
        collection.countDocuments({}),
        collection.findOne({}),
      ]);
      collections.push({
        name: collectionName,
        document_count: documentCount,
        sample_fields: sampleDoc ? Object.keys(sampleDoc).slice(0, 10) : [],
      });
    }
    return { collections };
  }

  async queryLog(dto: AgentLogQueryDto): Promise<{
    total: number;
    documents: Array<Record<string, unknown>>;
  }> {
    if (!this.allowedCollections.has(dto.collection)) {
      throw BusinessException.badRequest(Constants.AGENT_LOG_COLLECTION_FORBIDDEN);
    }
    const filter = dto.filter || {};
    const sort = dto.sort || { createdAt: -1 };
    this.validateQueryObject(filter);
    this.validateQueryObject(sort);

    const limit = Math.min(Math.max(dto.limit || 10, 1), 100);
    const collection = this.connection.collection(dto.collection);
    const [total, documents] = await Promise.all([
      collection.countDocuments(filter),
      collection.find(filter).sort(sort).limit(limit).toArray(),
    ]);
    return {
      total,
      documents: documents.map((doc) => this.serializeMongoValue(doc)),
    };
  }

  private validateQueryObject(value: unknown): void {
    if (Array.isArray(value)) {
      value.forEach((item) => this.validateQueryObject(item));
      return;
    }
    if (!value || typeof value !== 'object') {
      return;
    }
    for (const [key, child] of Object.entries(value)) {
      if (this.blockedOperators.has(key)) {
        throw BusinessException.badRequest(
          `${Constants.AGENT_LOG_OPERATOR_FORBIDDEN_PREFIX}${key}`,
        );
      }
      this.validateQueryObject(child);
    }
  }

  private serializeMongoValue(value: unknown): any {
    if (value instanceof Date) {
      return value.toISOString();
    }
    if (Array.isArray(value)) {
      return value.map((item) => this.serializeMongoValue(item));
    }
    if (value && typeof value === 'object') {
      if (
        '_bsontype' in value &&
        typeof (value as { toString?: unknown }).toString === 'function'
      ) {
        return (value as { toString: () => string }).toString();
      }
      const result: Record<string, unknown> = {};
      for (const [key, child] of Object.entries(value)) {
        result[key] = this.serializeMongoValue(child);
      }
      return result;
    }
    return value;
  }
}
