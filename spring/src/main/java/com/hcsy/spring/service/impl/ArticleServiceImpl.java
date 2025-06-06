package com.hcsy.spring.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.mapper.ArticleMapper;
import com.hcsy.spring.po.Article;
import com.hcsy.spring.service.ArticleService;

import java.util.List;

import org.springframework.stereotype.Service;

@Service
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements ArticleService {
    // 可扩展自定义实现
    @Override
    public List<Article> listPublishedArticles() {
        return lambdaQuery()
                .eq(Article::getStatus, 1)
                .list();
    }

    @Override
    public IPage<Article> listPublishedArticles(Page<Article> page) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getStatus, 1); // 只查已发布
        queryWrapper.orderByAsc(Article::getCreatedAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

}
