import { Injectable } from '@nestjs/common';
import * as jwt from 'jsonwebtoken';
import { ConfigService } from '@nestjs/config';
import { BusinessException } from '../exceptions/business.exception';
import { Constants } from './constants';

interface InternalTokenClaims {
  userId: number;
  serviceName: string;
  tokenType: string;
  iat?: number;
  exp?: number;
}

/**
 * 内部服务令牌工具类
 * 用于生成和验证内部服务之间通信的JWT令牌
 */
@Injectable()
export class InternalTokenUtil {
  private secret: string;
  private expiration: number;

  constructor(private readonly configService: ConfigService) {
    this.secret = this.configService.get<string>('internal-token.secret')!;
    this.expiration = this.configService.get<number>(
      'internal-token.expiration',
    )!;

    if (!this.secret) {
      throw new BusinessException(
        Constants.INTERNAL_TOKEN_SECRET_NOT_CONFIGURED,
      );
    }
  }

  /**
   * 生成内部服务令牌
   * @param userId 用户ID（-1表示系统调用）
   * @param serviceName 服务名称
   * @returns JWT令牌字符串
   */
  async generateInternalToken(
    userId: number,
    serviceName: string,
  ): Promise<string> {
    const claims: InternalTokenClaims = {
      userId,
      serviceName,
      tokenType: 'internal',
    };

    // 计算过期时间（毫秒转秒）
    const expiresIn = Math.floor(this.expiration / 1000);

    return jwt.sign(claims, this.secret, { expiresIn });
  }

  /**
   * 验证内部服务令牌
   * @param token JWT令牌字符串
   * @returns 验证成功返回解密后的声明，失败抛出异常
   */
  async validateInternalToken(token: string): Promise<InternalTokenClaims> {
    try {
      const decoded: unknown = jwt.verify(token, this.secret);
      return decoded as InternalTokenClaims;
    } catch (error: unknown) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new BusinessException(Constants.INTERNAL_TOKEN_EXPIRED);
      }
      throw new BusinessException(Constants.INTERNAL_TOKEN_INVALID);
    }
  }

  /**
   * 从令牌中提取用户ID
   * @param token JWT令牌字符串
   * @returns 用户ID
   */
  async extractUserId(token: string): Promise<number> {
    const claims = await this.validateInternalToken(token);
    return claims.userId;
  }

  /**
   * 从令牌中提取服务名称
   * @param token JWT令牌字符串
   * @returns 服务名称
   */
  async extractServiceName(token: string): Promise<string> {
    const claims = await this.validateInternalToken(token);
    return claims.serviceName;
  }
}
