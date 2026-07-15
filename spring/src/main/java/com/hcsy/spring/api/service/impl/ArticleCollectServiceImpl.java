package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.ArticleCollectMapper;
import com.hcsy.spring.api.mapper.ArticleMapper;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.mapper.UserMapper;
import com.hcsy.spring.api.service.ArticleCollectService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleCollectVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class ArticleCollectServiceImpl extends ServiceImpl<ArticleCollectMapper, ArticleCollect>
        implements ArticleCollectService {

    private final ArticleCollectMapper articleCollectMapper;
    private final ArticleMapper articleMapper;
    private final UserMapper userMapper;
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;

    @Override
    @Transactional
    @ArticleSync(action = "collect", description = "收藏了1篇文章")
    public boolean addCollect(Long articleId, Long userId) {
        // 检查是否已经收藏
        if (isCollected(articleId, userId)) {
            return false;
        }

        ArticleCollect collect = new ArticleCollect();
        collect.setArticleId(articleId);
        collect.setUserId(userId);
        collect.setCreatedTime(LocalDateTime.now());

        return articleCollectMapper.insert(collect) > 0;
    }

    @SuppressWarnings("null")
    @Override
    @Transactional
    @ArticleSync(action = "uncollect", description = "取消收藏了1篇文章")
    public boolean removeCollect(Long articleId, Long userId) {
        LambdaQueryWrapper<ArticleCollect> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(ArticleCollect::getArticleId, articleId);
        queryWrapper.eq(ArticleCollect::getUserId, userId);

        return articleCollectMapper.delete(queryWrapper) > 0;
    }

    @SuppressWarnings("null")
    @Override
    public boolean isCollected(Long articleId, Long userId) {
        LambdaQueryWrapper<ArticleCollect> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(ArticleCollect::getArticleId, articleId);
        queryWrapper.eq(ArticleCollect::getUserId, userId);

        return articleCollectMapper.selectOne(queryWrapper) != null;
    }

    @SuppressWarnings("null")
    @Override
    public IPage<ArticleCollectVO> listUserCollects(Long userId, Page<ArticleCollect> page) {
        LambdaQueryWrapper<ArticleCollect> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(ArticleCollect::getUserId, userId);
        queryWrapper.orderByDesc(ArticleCollect::getCreatedTime);

        IPage<ArticleCollect> collectPage = this.page(page, queryWrapper);

        // 转换为VO，并关联文章、作者、分类信息
        List<ArticleCollectVO> voList = collectPage.getRecords().stream().map(
                collect -> {
                    Article article = articleMapper.selectById(collect.getArticleId());
                    if (article == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_ARTICLE_ID + collect.getArticleId()).build();
                    }
                    ArticleCollectVO vo = BeanUtil.copyProperties(article, ArticleCollectVO.class);
                    vo.setArticleCreateAt(article.getCreateAt());
                    vo.setArticleUpdateAt(article.getUpdateAt());

                    vo.setId(collect.getId());
                    vo.setArticleId(collect.getArticleId());
                    vo.setCollectedTime(collect.getCreatedTime());

                    // 获取作者信息
                    if (article.getUserId() == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_ARTICLE_ID_AUTHOR_ID + article.getId()).build();
                    }
                    User author = userMapper.selectById(article.getUserId());
                    if (author == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_ARTICLE_AUTHOR_ID + article.getUserId()).build();
                    }
                    vo.setAuthorName(author.getName());

                    // 获取分类信息
                    if (article.getSubCategoryId() == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_SUB_CATEGORY_ID_AUTHOR_ID + article.getId()).build();
                    }
                    SubCategory subCategory = subCategoryMapper.selectById(article.getSubCategoryId());
                    if (subCategory == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_SUB_CATEGORY_AUTHOR_ID + article.getSubCategoryId()).build();
                    }
                    vo.setSubCategoryName(subCategory.getName());
                    // 获取父分类
                    if (subCategory.getCategoryId() == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_CATEGORY_ID_AUTHOR_ID + subCategory.getId()).build();
                    }
                    Category category = categoryMapper.selectById(subCategory.getCategoryId());
                    if (category == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_CATEGORY_AUTHOR_ID + subCategory.getCategoryId()).build();
                    }
                    vo.setCategoryName(category.getName());

                    return vo;
                }).collect(Collectors.toList());

        // 创建新的IPage对象返回VO列表
        Page<ArticleCollectVO> voPage = new Page<>(collectPage.getCurrent(), collectPage.getSize());
        voPage.setRecords(voList);
        voPage.setTotal(collectPage.getTotal());

        return voPage;
    }

    @SuppressWarnings("null")
    @Override
    public Long getCollectCountByArticleId(Long articleId) {
        LambdaQueryWrapper<ArticleCollect> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(ArticleCollect::getArticleId, articleId);
        return articleCollectMapper.selectCount(queryWrapper);
    }
}
