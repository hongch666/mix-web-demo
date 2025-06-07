package com.hcsy.spring.service;

import java.util.List;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.po.Article;

public interface ArticleService extends IService<Article> {
    List<Article> listPublishedArticles();

    IPage<Article> listPublishedArticles(Page<Article> page);

    boolean saveArticle(Article article);

    boolean updateArticle(Article article);

    boolean deleteArticle(Long id);

}
