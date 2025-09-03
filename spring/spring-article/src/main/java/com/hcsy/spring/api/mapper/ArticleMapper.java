package com.hcsy.spring.api.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.Article;

import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ArticleMapper extends BaseMapper<Article> {
    // 可自定义扩展方法
}
