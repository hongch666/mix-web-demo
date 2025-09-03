package com.hcsy.spring.api.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.User;

import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 继承 BaseMapper 自动拥有基本的 CRUD 方法
}
