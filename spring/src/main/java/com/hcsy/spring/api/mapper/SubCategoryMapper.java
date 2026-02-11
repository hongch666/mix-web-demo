package com.hcsy.spring.api.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.SubCategory;

import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface SubCategoryMapper extends BaseMapper<SubCategory> {
    // 可自定义扩展方法
}
