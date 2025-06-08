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
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements ArticleService {
    private final ArticleMapper articleMapper;

    // 可扩展自定义实现
    @Override
    @Transactional
    public List<Article> listPublishedArticles() {
        return lambdaQuery()
                .eq(Article::getStatus, 1)
                .list();
    }

    @Override
    @Transactional
    public IPage<Article> listPublishedArticles(Page<Article> page) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getStatus, 1); // 只查已发布
        queryWrapper.orderByAsc(Article::getCreatedAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    @Transactional
    public IPage<Article> listArticlesById(Page<Article> page, Integer id) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getUserId, id);
        queryWrapper.orderByAsc(Article::getCreatedAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    @Transactional
    public boolean saveArticle(Article article) {
        articleMapper.insert(article);
        return true;
    }

    @Override
    @Transactional
    public boolean updateArticle(Article article) {
        articleMapper.updateById(article);
        return true;
    }

    @Override
    @Transactional
    public boolean deleteArticle(Long id) {
        articleMapper.deleteById(id);
        return true;
    }

    @Override
    public void publishArticle(Long id) {
        Article article = new Article();
        article.setId(id);
        article.setStatus(1); // 发布状态

        boolean updated = updateById(article);
        if (!updated) {
            throw new RuntimeException("发布失败：文章不存在或更新失败");
        }
    }

    @Override
    public List<Article> listUnpublishedArticles() {
        return articleMapper.selectList(
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));
    }

}
