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
import com.hcsy.spring.api.mapper.ArticleLikeMapper;
import com.hcsy.spring.api.mapper.ArticleMapper;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.mapper.UserMapper;
import com.hcsy.spring.api.service.ArticleLikeService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleLikeVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class ArticleLikeServiceImpl extends ServiceImpl<ArticleLikeMapper, ArticleLike> implements ArticleLikeService {

    private final ArticleLikeMapper articleLikeMapper;
    private final ArticleMapper articleMapper;
    private final UserMapper userMapper;
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;

    @Override
    @Transactional
    @ArticleSync(action = "like", description = "点赞了1篇文章")
    public boolean addLike(Long articleId, Long userId) {
        // 检查是否已经点赞
        if (isLiked(articleId, userId)) {
            return false;
        }

        ArticleLike like = new ArticleLike();
        like.setArticleId(articleId);
        like.setUserId(userId);
        like.setCreatedTime(LocalDateTime.now());

        return articleLikeMapper.insert(like) > 0;
    }

    @SuppressWarnings("null")
    @Override
    @Transactional
    @ArticleSync(action = "unlike", description = "取消点赞了1篇文章")
    public boolean removeLike(Long articleId, Long userId) {
        LambdaQueryWrapper<ArticleLike> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(ArticleLike::getArticleId, articleId);
        queryWrapper.eq(ArticleLike::getUserId, userId);

        return articleLikeMapper.delete(queryWrapper) > 0;
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public boolean isLiked(Long articleId, Long userId) {
        LambdaQueryWrapper<ArticleLike> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(ArticleLike::getArticleId, articleId);
        queryWrapper.eq(ArticleLike::getUserId, userId);

        return articleLikeMapper.selectOne(queryWrapper) != null;
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public IPage<ArticleLikeVO> listUserLikes(Long userId, Page<ArticleLike> page) {
        LambdaQueryWrapper<ArticleLike> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(ArticleLike::getUserId, userId);
        queryWrapper.orderByDesc(ArticleLike::getCreatedTime);

        IPage<ArticleLike> likePage = this.page(page, queryWrapper);

        // 转换为VO，并关联文章、作者、分类信息
        List<ArticleLikeVO> voList = likePage.getRecords().stream().map(
                like -> {
                    Article article = articleMapper.selectById(like.getArticleId());

                    if (article == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_ARTICLE_ID + like.getArticleId()).build();
                    }
                    ArticleLikeVO vo = BeanUtil.copyProperties(article, ArticleLikeVO.class);
                    vo.setArticleCreateAt(article.getCreateAt());
                    vo.setArticleUpdateAt(article.getUpdateAt());

                    vo.setId(like.getId());
                    vo.setArticleId(like.getArticleId());
                    vo.setLikedTime(like.getCreatedTime());

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
        Page<ArticleLikeVO> voPage = new Page<>(likePage.getCurrent(), likePage.getSize());
        voPage.setRecords(voList);
        voPage.setTotal(likePage.getTotal());

        return voPage;
    }

    @Transactional(readOnly = true)
    @SuppressWarnings("null")
    @Override
    public Long getLikeCountByArticleId(Long articleId) {
        LambdaQueryWrapper<ArticleLike> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(ArticleLike::getArticleId, articleId);
        return articleLikeMapper.selectCount(queryWrapper);
    }
}
