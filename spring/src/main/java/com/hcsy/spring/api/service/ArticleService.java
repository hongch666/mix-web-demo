package com.hcsy.spring.api.service;

import java.util.List;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.po.Article;

public interface ArticleService extends IService<Article> {
    List<Article> listPublishedArticles();

    IPage<Article> listPublishedArticles(Page<Article> page);

    boolean saveArticle(Article article);

    boolean updateArticle(Article article);

    boolean deleteArticle(Long id);

    boolean deleteArticles(List<Long> ids);

    IPage<Article> listArticlesById(Page<Article> page, Integer id);

    void publishArticle(Long id);

    void addViewArticle(Long id);

    List<Article> listUnpublishedArticles();

    Article findByArticleTitle(String articleTitle);

    List<Article> listAllArticlesByTitle(String articleTitle);

}
