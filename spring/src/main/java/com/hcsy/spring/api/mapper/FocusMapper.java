package com.hcsy.spring.api.mapper;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.Focus;

@Mapper
public interface FocusMapper extends BaseMapper<Focus> {
    // 可自定义扩展方法
}
