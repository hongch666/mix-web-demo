package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.ArticleMapper;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.CategoryService;
import com.hcsy.spring.api.service.SubCategoryService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements ArticleService {
    private final UserService userService;
    private final CategoryService categoryService;
    private final SubCategoryService subCategoryService;

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public List<Article> listPublishedArticles() {
        return lambdaQuery()
                .eq(Article::getStatus, 1)
                .list();
    }

    @Transactional(readOnly = true)
    @Override
    public IPage<ArticleWithCategoryVO> listArticlesByIdWithCategory(Page<Article> page, Integer id, boolean onlyPublished) {
        IPage<Article> resultPage = listArticlesById(page, id, onlyPublished);

        List<Article> records = resultPage.getRecords();
        if (records.isEmpty()) {
            Page<ArticleWithCategoryVO> emptyPage = new Page<>(page.getCurrent(), page.getSize(), 0);
            emptyPage.setRecords(Collections.emptyList());
            return emptyPage;
        }

        // 批量查询关联数据，避免 N+1 问题
        Map<Long, User> userMap = batchQueryUsers(records);
        Map<Long, SubCategory> subCategoryMap = batchQuerySubCategories(records);
        Map<Long, Category> categoryMap = batchQueryCategories(subCategoryMap.values());

        // 转换为VO对象并补充分类和用户信息
        List<ArticleWithCategoryVO> voList = records.stream().map(article -> {
            if (article.getSubCategoryId() == null) {
                throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_SUB_CATEGORY_ID).build();
            }

            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);

            User user = userMap.get(article.getUserId());
            vo.setUsername(user != null ? user.getName() : Defaults.DEFAULT_USER);

            SubCategory subCategory = subCategoryMap.get(article.getSubCategoryId().longValue());
            if (subCategory != null) {
                vo.setSubCategoryName(subCategory.getName());
                Category category = categoryMap.get(subCategory.getCategoryId());
                if (category != null) {
                    vo.setCategoryName(category.getName());
                }
            }

            return vo;
        }).toList();

        // 创建新的IPage对象，包含转换后的VO列表
        Page<ArticleWithCategoryVO> voPage = new Page<>(page.getCurrent(), page.getSize(), resultPage.getTotal());
        voPage.setRecords(voList);
        return voPage;
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public IPage<Article> listPublishedArticles(Page<Article> page) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getStatus, 1); // 只查已发布
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public IPage<Article> listArticlesById(Page<Article> page, Integer id) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getUserId, id);
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
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
        this.baseMapper.insert(article);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "edit", description = "编辑了1篇文章")
    public boolean updateArticle(Article article) {
        this.baseMapper.updateById(article);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "delete", description = "删除了1篇文章")
    public boolean deleteArticle(Long id) {
        Article existing = this.baseMapper.selectById(id);
        if (existing == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_ARTICLE_ID + id).build();
        }
        this.baseMapper.deleteById(id);
        return true;
    }

    @Override
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

        List<Article> existingList = this.baseMapper.selectBatchIds(distinctIds);
        if (existingList.size() != distinctIds.size()) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_ARTICLES).build();
        }

        this.baseMapper.deleteBatchIds(ids);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "publish", description = "发布了1篇文章")
    public void publishArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = this.baseMapper.selectById(id);
        if (dbArticle == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_ARTICLE).build();
        }

        // 执行发布
        Article article = new Article();
        article.setId(id);
        article.setStatus(1); // 发布状态

        boolean updated = updateById(article);
        if (!updated) {
            throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.PUBLISH_ARTICLE).build();
        }
    }

    @Override
    @Transactional
    @ArticleSync(action = "view", description = "浏览了1篇文章")
    public void addViewArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = this.baseMapper.selectById(id);
        if (dbArticle == null) {
            throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_ARTICLE).build();
        }
        if (dbArticle.getStatus() != 1) {
            throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.UNPUBLISH_ADD_VIEW).build();
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
            throw BusinessException.builder().httpStatus(HttpCode.UNPROCESSABLE_ENTITY).errorMessage(Messages.ADD_VIEW_ARTICLE).build();
        }
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public List<Article> listUnpublishedArticles() {
        return this.baseMapper.selectList(
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public IPage<Article> listUnpublishedArticles(Page<Article> page) {
        return this.baseMapper.selectPage(page,
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));
    }

    @Transactional(readOnly = true)
    @Override
    public IPage<ArticleWithCategoryVO> listUnpublishedArticlesWithCategory(Page<Article> page) {
        @SuppressWarnings("null")
        IPage<Article> resultPage = this.baseMapper.selectPage(page,
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));

        List<Article> records = resultPage.getRecords();
        if (records.isEmpty()) {
            Page<ArticleWithCategoryVO> emptyPage = new Page<>(page.getCurrent(), page.getSize(), 0);
            emptyPage.setRecords(Collections.emptyList());
            return emptyPage;
        }

        // 批量查询关联数据，避免 N+1 问题
        Map<Long, User> userMap = batchQueryUsers(records);
        Map<Long, SubCategory> subCategoryMap = batchQuerySubCategories(records);
        Map<Long, Category> categoryMap = batchQueryCategories(subCategoryMap.values());

        // 转换为VO对象并补充分类信息
        List<ArticleWithCategoryVO> voList = records.stream().map(article -> {
            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);

            User user = userMap.get(article.getUserId());
            vo.setUsername(user != null ? user.getName() : Defaults.DEFAULT_USER);

            if (article.getSubCategoryId() != null) {
                SubCategory subCategory = subCategoryMap.get(article.getSubCategoryId().longValue());
                if (subCategory != null) {
                    vo.setSubCategoryName(subCategory.getName());
                    Category category = categoryMap.get(subCategory.getCategoryId());
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

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public Article findByArticleTitle(String articleTitle) {
        return this.baseMapper.selectOne(
                new LambdaQueryWrapper<Article>().eq(Article::getTitle, articleTitle));
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public List<Article> listAllArticlesByTitle(String articleTitle) {
        return this.baseMapper.selectList(
                new LambdaQueryWrapper<Article>().like(Article::getTitle, articleTitle));
    }

    /**
     * 批量查询文章列表中的用户信息，返回 userId -> User 映射
     */
    @SuppressWarnings("null")
    private Map<Long, User> batchQueryUsers(List<Article> articles) {
        Set<Long> userIds = articles.stream()
                .map(Article::getUserId)
                .filter(id -> id != null)
                .collect(Collectors.toSet());
        if (userIds.isEmpty()) {
            return Collections.emptyMap();
        }
        return userService.listByIds(userIds).stream()
                .collect(Collectors.toMap(User::getId, Function.identity()));
    }

    /**
     * 批量查询文章列表中的子分类信息，返回 subCategoryId -> SubCategory 映射
     */
    @SuppressWarnings("null")
    private Map<Long, SubCategory> batchQuerySubCategories(List<Article> articles) {
        Set<Long> subCategoryIds = articles.stream()
                .map(Article::getSubCategoryId)
                .filter(id -> id != null)
                .map(Integer::longValue)
                .collect(Collectors.toSet());
        if (subCategoryIds.isEmpty()) {
            return Collections.emptyMap();
        }
        return subCategoryService.listByIds(subCategoryIds).stream()
                .collect(Collectors.toMap(SubCategory::getId, Function.identity()));
    }

    /**
     * 根据子分类集合批量查询主分类信息，返回 categoryId -> Category 映射
     */
    @SuppressWarnings("null")
    private Map<Long, Category> batchQueryCategories(java.util.Collection<SubCategory> subCategories) {
        Set<Long> categoryIds = subCategories.stream()
                .map(SubCategory::getCategoryId)
                .filter(id -> id != null)
                .collect(Collectors.toSet());
        if (categoryIds.isEmpty()) {
            return Collections.emptyMap();
        }
        return categoryService.listByIds(categoryIds).stream()
                .collect(Collectors.toMap(Category::getId, Function.identity()));
    }

}
