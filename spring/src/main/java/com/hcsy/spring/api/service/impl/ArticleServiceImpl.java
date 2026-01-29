package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.ArticleMapper;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import cn.hutool.core.bean.BeanUtil;
import com.hcsy.spring.common.annotation.ArticleSync;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.User;

import lombok.RequiredArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements ArticleService {
    private final ArticleMapper articleMapper;
    private final UserService userService;
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;

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
    public IPage<Article> listArticlesById(Page<Article> page, Integer id, boolean onlyPublished) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getUserId, id);
        if (onlyPublished) {
            queryWrapper.eq(Article::getStatus, 1); // 只查已发布
        }
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    @Transactional
    @ArticleSync(action = "add", description = "创建了1篇文章")
    public boolean saveArticle(Article article) {
        articleMapper.insert(article);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "edit", description = "编辑了1篇文章")
    public boolean updateArticle(Article article) {
        articleMapper.updateById(article);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "delete", description = "删除了1篇文章")
    public boolean deleteArticle(Long id) {
        Article existing = articleMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(Constants.UNDEFINED_ARTICLE_ID + id);
        }
        articleMapper.deleteById(id);
        return true;
    }

    @Transactional
    @ArticleSync(action = "delete", description = "批量删除文章")
    public boolean deleteArticles(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return true;
        }

        // 批量删除前校验：必须全部存在（只要有一个不存在就抛异常）
        List<Long> distinctIds = ids.stream()
                .filter(id -> id != null)
                .distinct()
                .toList();
        if (distinctIds.isEmpty()) {
            return true;
        }

        List<Article> existingList = articleMapper.selectBatchIds(distinctIds);
        if (existingList.size() != distinctIds.size()) {
            throw new BusinessException(Constants.UNDEFINED_ARTICLE);
        }

        articleMapper.deleteBatchIds(ids);
        return true;
    }

    @Override
    @ArticleSync(action = "publish", description = "发布了1篇文章")
    public void publishArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        if (dbArticle == null) {
            throw new BusinessException(Constants.UNDEFINED_ARTICLE);
        }

        // 执行发布
        Article article = new Article();
        article.setId(id);
        article.setStatus(1); // 发布状态

        boolean updated = updateById(article);
        if (!updated) {
            throw new BusinessException(Constants.PUBLISH_ARTICLE);
        }
    }

    @Override
    @ArticleSync(action = "view", description = "浏览了1篇文章")
    public void addViewArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        if (dbArticle == null) {
            throw new BusinessException(Constants.UNDEFINED_ARTICLE);
        }
        if (dbArticle.getStatus() != 1) {
            throw new BusinessException(Constants.UNPUBLISH_ADD_VIEW);
        }
        // 获取当前的文章的修改日期
        LocalDateTime updateAt = dbArticle.getUpdateAt();
        // 增加阅读量
        Article article = new Article();
        article.setId(id);
        article.setViews(dbArticle.getViews() + 1); // 发布状态
        article.setUpdateAt(updateAt); // 保持原有的更新时间

        boolean updated = updateById(article);
        if (!updated) {
            throw new BusinessException(Constants.ADD_VIEW_ARTICLE);
        }
    }

    @Override
    public List<Article> listUnpublishedArticles() {
        return articleMapper.selectList(
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));
    }

    @Override
    public IPage<Article> listUnpublishedArticles(Page<Article> page) {
        return articleMapper.selectPage(page,
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));
    }

    @Override
    public IPage<ArticleWithCategoryVO> listUnpublishedArticlesWithCategory(Page<Article> page) {
        IPage<Article> resultPage = articleMapper.selectPage(page,
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));

        // 转换为VO对象并补充分类信息
        List<ArticleWithCategoryVO> voList = resultPage.getRecords().stream().map(article -> {
            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);

            // 查询作者用户名
            User user = userService.getById(article.getUserId());
            vo.setUsername(user != null ? user.getName() : Constants.DEFAULT_USER);

            // 查询子分类和主分类信息
            if (article.getSubCategoryId() != null) {
                SubCategory subCategory = subCategoryMapper.selectById(article.getSubCategoryId());
                if (subCategory != null) {
                    vo.setSubCategoryName(subCategory.getName());
                    // 查询主分类信息
                    Category category = categoryMapper.selectById(subCategory.getCategoryId());
                    if (category != null) {
                        vo.setCategoryId(category.getId());
                        vo.setCategoryName(category.getName());
                    }
                }
            }

            return vo;
        }).toList();

        // 创建新的IPage对象，包含转换后的VO列表
        Page<ArticleWithCategoryVO> voPage = new Page<>(page.getCurrent(), page.getSize(), resultPage.getTotal());
        voPage.setRecords(voList);
        return voPage;
    }

    @Override
    public Article findByArticleTitle(String articleTitle) {
        return articleMapper.selectOne(
                new LambdaQueryWrapper<Article>().eq(Article::getTitle, articleTitle));
    }

    @Override
    public List<Article> listAllArticlesByTitle(String articleTitle) {
        return articleMapper.selectList(
                new LambdaQueryWrapper<Article>().like(Article::getTitle, articleTitle));
    }

}
