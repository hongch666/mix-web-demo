import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Like } from 'typeorm';
import { User } from './entities/user.entity';

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  // 查询用户
  async getUserById(id: number): Promise<User | null> {
    return this.userRepository.findOne({ where: { id } });
  }

  // 根据用户名模糊搜索用户
  async getUsersByName(name: string): Promise<User[]> {
    return this.userRepository.find({
      where: { name: Like(`%${name}%`) },
    });
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
}
