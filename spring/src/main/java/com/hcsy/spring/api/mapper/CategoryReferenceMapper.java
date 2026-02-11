package com.hcsy.spring.api.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.CategoryReference;

import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CategoryReferenceMapper extends BaseMapper<CategoryReference> {
    // 可自定义扩展方法
}
