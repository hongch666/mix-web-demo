import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { InjectRepository } from '@nestjs/typeorm';
import * as bcrypt from 'bcrypt';
import { Like, Repository } from 'typeorm';
import { User } from './entities/user.entity';

export interface GithubUserProfile {
  githubId: string;
  githubLogin: string;
  githubName: string | null;
  githubUrl: string | null;
  avatarUrl: string | null;
  email: string | null;
}

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
    private readonly configService: ConfigService,
  ) {}

  private readonly saltRounds = 10;

  // 查询用户
  async getUserById(id: number): Promise<User | null> {
    return this.userRepository.findOne({ where: { id } });
  }

  // 根据用户名模糊搜索用户
  async getUsersByName(name: string): Promise<User[]> {
    return this.userRepository.find({
      where: [{ name: Like(`%${name}%`) }, { githubLogin: Like(`%${name}%`) }],
    });
  }

  // 根据 GitHub ID 查询用户
  async getUserByGithubId(githubId: string): Promise<User | null> {
    return this.userRepository.findOne({ where: { githubId } });
  }

  // 创建或更新 GitHub 用户
  async findOrCreateGithubUser(profile: GithubUserProfile): Promise<User> {
    const existingUser: User | null = await this.getUserByGithubId(
      profile.githubId,
    );
    const availableEmail: string | null = await this.resolveAvailableEmail(
      profile.email,
      existingUser?.id,
    );

    if (existingUser) {
      existingUser.githubLogin = profile.githubLogin;
      existingUser.githubUrl = profile.githubUrl;
      existingUser.img = profile.avatarUrl;
      existingUser.email = availableEmail ?? existingUser.email;
      existingUser.authProvider = 'github';
      existingUser.lastLoginAt = new Date();
      return this.userRepository.save(existingUser);
    }

    // 首次登录注册：使用默认密码的 bcrypt 加密值
    const rawDefaultPassword: string = this.configService.get<string>(
      'USER_DEFAULT_PASSWORD',
    )!;
    const encryptedPassword: string = await bcrypt.hash(
      rawDefaultPassword,
      this.saltRounds,
    );

    const user: User = this.userRepository.create({
      githubId: profile.githubId,
      githubLogin: profile.githubLogin,
      githubUrl: profile.githubUrl,
      name: await this.buildUniqueGithubUsername(profile),
      password: encryptedPassword,
      email: availableEmail,
      role: 'user',
      img: profile.avatarUrl,
      age: 18,
      authProvider: 'github',
      lastLoginAt: new Date(),
    });

    return this.userRepository.save(user);
  }

  // 判断用户是否是管理员
  async isAdminUser(userId: number): Promise<boolean> {
    const user = await this.userRepository.findOne({ where: { id: userId } });
    if (!user) {
      return false;
    }
    // 根据role字段判断是否是管理员，支持'admin'、'ADMIN'等多种格式
    return (user.role ?? '').toLowerCase() === 'admin';
  }

  private async buildUniqueGithubUsername(
    profile: GithubUserProfile,
  ): Promise<string> {
    const preferredName: string =
      profile.githubName?.trim() ||
      profile.githubLogin.trim() ||
      `github_${profile.githubId}`;

    const preferredExists: User | null = await this.userRepository.findOne({
      where: { name: preferredName },
    });
    if (!preferredExists) {
      return preferredName;
    }

    const fallbackBase: string = `github_${profile.githubLogin || 'user'}_${profile.githubId}`;
    const fallbackExists: User | null = await this.userRepository.findOne({
      where: { name: fallbackBase },
    });
    if (!fallbackExists) {
      return fallbackBase;
    }

    let suffix = 1;
    while (true) {
      const candidate = `${fallbackBase}_${suffix}`;
      const existing: User | null = await this.userRepository.findOne({
        where: { name: candidate },
      });
      if (!existing) {
        return candidate;
      }
      suffix += 1;
    }
  }

  private async resolveAvailableEmail(
    email: string | null,
    currentUserId?: number,
  ): Promise<string | null> {
    if (!email) {
      return null;
    }

    const existingUser: User | null = await this.userRepository.findOne({
      where: { email },
    });
    if (existingUser && existingUser.id !== currentUserId) {
      return null;
    }

    return email;
  }
}
