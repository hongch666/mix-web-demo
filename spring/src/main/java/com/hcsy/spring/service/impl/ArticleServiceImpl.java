package com.hcsy.spring.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.mapper.ArticleMapper;
import com.hcsy.spring.po.Article;
import com.hcsy.spring.service.ArticleService;

import lombok.RequiredArgsConstructor;

import java.util.List;

import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements ArticleService {
    private final ArticleMapper articleMapper;

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

    @Override
    public IPage<Article> listArticlesById(Page<Article> page, Integer id) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getUserId, id);
        queryWrapper.orderByAsc(Article::getCreatedAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    public boolean saveArticle(Article article) {
        articleMapper.insert(article);
        return true;
    }

    @Override
    public boolean updateArticle(Article article) {
        articleMapper.updateById(article);
        return true;
    }

    @Override
    public boolean deleteArticle(Long id) {
        articleMapper.deleteById(id);
        return true;
    }

}
