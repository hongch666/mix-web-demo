// src/user/user.controller.ts
import { Controller, Get, Post, Body } from '@nestjs/common';
import { UserService } from './user.service';
import { User } from './entity/user.entity';
import { ApiOperation, ApiTags } from '@nestjs/swagger';

@Controller('users')
@ApiTags('测试模块')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get()
  @ApiOperation({ summary: '获取用户信息', description: '获取用户信息列表' })
  findAll(): Promise<User[]> {
    return this.userService.findAll();
  }

  @Post()
  @ApiOperation({ summary: '新增用户', description: '通过请求体创建用户信息' })
  create(@Body() userData: Partial<User>): Promise<User> {
    return this.userService.create(userData);
  }
}
