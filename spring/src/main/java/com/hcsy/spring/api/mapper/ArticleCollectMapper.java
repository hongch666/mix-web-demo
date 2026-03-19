package com.hcsy.spring.api.mapper;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.ArticleCollect;

@Mapper
public interface ArticleCollectMapper extends BaseMapper<ArticleCollect> {
    // 可自定义扩展方法
}
