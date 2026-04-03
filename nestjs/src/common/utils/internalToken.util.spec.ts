import { ConfigService } from '@nestjs/config';
import { Test, TestingModule } from '@nestjs/testing';
import { InternalTokenUtil } from './internalToken.util';

describe('InternalTokenUtil', () => {
  let internalTokenUtil: InternalTokenUtil;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        InternalTokenUtil,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              if (key === 'internal-token.secret') {
                return 'abcdefghijklmnopqrstuvwxyz123456';
              }
              if (key === 'internal-token.expiration') {
                return 60000;
              }
              return undefined;
            }),
          },
        },
      ],
    }).compile();

    internalTokenUtil = module.get<InternalTokenUtil>(InternalTokenUtil);
  });

  it('应该生成可用的内部Token', async () => {
    const token = await internalTokenUtil.generateInternalToken(
      10001,
      'nestjs',
    );

    console.log(`生成的内部Token: ${token}`);
    expect(token).toBeTruthy();
    expect(token.length).toBeGreaterThan(0);
  });

  it('应该使用环境变量中的内部Token校验通过', async () => {
    const token = process.env.INTERNAL_TOKEN_TEST_TOKEN;

    expect(token).toBeTruthy();

    const claims = await internalTokenUtil.validateInternalToken(
      token as string,
    );

    expect(claims.userId).toBeDefined();
    expect(claims.serviceName).toBeDefined();
    expect(claims.tokenType).toBe('internal');
  });
});
