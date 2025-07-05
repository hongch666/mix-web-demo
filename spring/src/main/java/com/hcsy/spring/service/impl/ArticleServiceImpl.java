package com.hcsy.spring.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.mapper.ArticleMapper;
import com.hcsy.spring.po.Article;
import com.hcsy.spring.service.ArticleService;
import com.hcsy.spring.utils.UserContext;

import lombok.RequiredArgsConstructor;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements ArticleService {
    private final ArticleMapper articleMapper;

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
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    @Transactional
    public IPage<Article> listArticlesById(Page<Article> page, Integer id) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getUserId, id);
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

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
        // 校验用户
        Long currentUserId = UserContext.getUserId();
        if (currentUserId == null) {
            throw new RuntimeException("未登录，无法更新文章");
        }

        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(article.getId());
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!currentUserId.equals(dbArticle.getUserId())) {
            throw new RuntimeException("无权修改他人文章");
        }
        // 执行修改
        articleMapper.updateById(article);
        return true;
    }

    @Override
    @Transactional
    public boolean deleteArticle(Long id) {
        // 校验用户
        Long currentUserId = UserContext.getUserId();
        if (currentUserId == null) {
            throw new RuntimeException("未登录，无法更新文章");
        }

        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!currentUserId.equals(dbArticle.getUserId())) {
            throw new RuntimeException("无权删除他人文章");
        }
        // 执行删除
        articleMapper.deleteById(id);
        return true;
    }

    @Transactional
    public boolean deleteArticles(List<Long> ids) {
        Long currentUserId = UserContext.getUserId();
        if (currentUserId == null) {
            throw new RuntimeException("未登录，无法删除文章");
        }
        for (Long id : ids) {
            Article dbArticle = articleMapper.selectById(id);
            if (dbArticle == null) {
                throw new RuntimeException("文章不存在，ID:" + id);
            }
            if (!currentUserId.equals(dbArticle.getUserId())) {
                throw new RuntimeException("无权删除他人文章，ID:" + id);
            }
        }
        articleMapper.deleteBatchIds(ids);
        return true;
    }

    @Override
    public void publishArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }

        // 执行发布
        Article article = new Article();
        article.setId(id);
        article.setStatus(1); // 发布状态

        boolean updated = updateById(article);
        if (!updated) {
            throw new RuntimeException("发布失败：文章不存在或更新失败");
        }
    }

    @Override
    public void addViewArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        // 增加阅读量
        Article article = new Article();
        article.setId(id);
        article.setViews(dbArticle.getViews() + 1); // 发布状态

        boolean updated = updateById(article);
        if (!updated) {
            throw new RuntimeException("更新失败：文章不存在或更新失败");
        }
    }

    @Override
    public List<Article> listUnpublishedArticles() {
        return articleMapper.selectList(
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));
    }

}
