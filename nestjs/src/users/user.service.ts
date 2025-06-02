// src/user/user.service.ts
import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entity/user.entity';
import { UserUpdateDTO } from './dto';

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private userRepo: Repository<User>,
  ) {}

  async findAll(): Promise<User[]> {
    return this.userRepo.find();
  }

  async create(userData: Partial<User>) {
    const user = this.userRepo.create(userData);
    this.userRepo.save(user);
    return null;
  }

  async remove(id: number) {
    const result = await this.userRepo.delete(id);
    if (result.affected === 0) {
      throw new NotFoundException(`删除失败，未找到 ID 为 ${id} 的用户`);
    }
    return null;
  }

  async findOne(id: number): Promise<User> {
    const user = await this.userRepo.findOneBy({ id });
    if (!user) {
      throw new NotFoundException(`未找到 ID 为 ${id} 的用户`);
    }
    return user;
  }

  async update(dto: UserUpdateDTO) {
    const user = await this.findOne(dto.id);
    const updated = Object.assign(user, dto);
    this.userRepo.save(updated);
    return null;
  }
}
