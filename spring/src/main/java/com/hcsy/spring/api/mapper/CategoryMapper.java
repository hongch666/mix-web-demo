package com.hcsy.spring.api.mapper;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.Category;

@Mapper
public interface CategoryMapper extends BaseMapper<Category> {
    // 可自定义扩展方法
}
