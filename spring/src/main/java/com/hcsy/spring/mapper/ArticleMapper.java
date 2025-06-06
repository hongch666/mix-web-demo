package com.hcsy.spring.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.po.Article;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ArticleMapper extends BaseMapper<Article> {
    // 可自定义扩展方法
}
