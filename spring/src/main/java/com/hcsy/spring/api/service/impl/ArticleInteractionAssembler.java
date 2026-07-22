package com.hcsy.spring.api.service.impl;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.stereotype.Component;

import com.hcsy.spring.api.repository.ArticleRepository;
import com.hcsy.spring.api.repository.CategoryRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.api.repository.UserRepository;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleCollectVO;
import com.hcsy.spring.entity.vo.ArticleLikeVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
class ArticleInteractionAssembler {

    private final ArticleRepository articleRepository;
    private final UserRepository userRepository;
    private final SubCategoryRepository subCategoryRepository;
    private final CategoryRepository categoryRepository;

    @SuppressWarnings("null")
    Mono<List<ArticleCollectVO>> toCollectVOs(List<ArticleCollect> interactions) {
        return loadRelations(interactions.stream().map(ArticleCollect::getArticleId).collect(Collectors.toSet()))
                .map(relations -> interactions.stream()
                        .map(interaction -> toCollectVO(interaction, relations))
                        .toList());
    }

    @SuppressWarnings("null")
    Mono<List<ArticleLikeVO>> toLikeVOs(List<ArticleLike> interactions) {
        return loadRelations(interactions.stream().map(ArticleLike::getArticleId).collect(Collectors.toSet()))
                .map(relations -> interactions.stream()
                        .map(interaction -> toLikeVO(interaction, relations))
                        .toList());
    }

    @SuppressWarnings("null")
    private Mono<Relations> loadRelations(Set<Long> articleIds) {
        return articleRepository.findAllById(articleIds)
                .collectMap(Article::getId, Function.identity())
                .flatMap(articles -> {
                    Set<Long> userIds = articles.values().stream().map(Article::getUserId)
                            .filter(id -> id != null).collect(Collectors.toSet());
                    Set<Long> subCategoryIds = articles.values().stream().map(Article::getSubCategoryId)
                            .filter(id -> id != null).map(Integer::longValue).collect(Collectors.toSet());
                    Mono<Map<Long, User>> users = userRepository.findAllById(userIds)
                            .collectMap(User::getId, Function.identity());
                    Mono<Map<Long, SubCategory>> subCategories = subCategoryRepository.findAllById(subCategoryIds)
                            .collectMap(SubCategory::getId, Function.identity());
                    return Mono.zip(users, subCategories).flatMap(result -> {
                        Set<Long> categoryIds = result.getT2().values().stream().map(SubCategory::getCategoryId)
                                .filter(id -> id != null).collect(Collectors.toSet());
                        return categoryRepository.findAllById(categoryIds)
                                .collectMap(Category::getId, Function.identity())
                                .map(categories -> new Relations(articles, result.getT1(), result.getT2(), categories));
                    });
                });
    }

    private ArticleCollectVO toCollectVO(ArticleCollect interaction, Relations relations) {
        Article article = requireArticle(interaction.getArticleId(), relations);
        ArticleCollectVO vo = BeanUtil.copyProperties(article, ArticleCollectVO.class);
        fillArticleRelations(article, vo, relations);
        vo.setId(interaction.getId());
        vo.setArticleId(interaction.getArticleId());
        vo.setArticleCreateAt(article.getCreateAt());
        vo.setArticleUpdateAt(article.getUpdateAt());
        vo.setCollectedTime(interaction.getCreatedTime());
        return vo;
    }

    private ArticleLikeVO toLikeVO(ArticleLike interaction, Relations relations) {
        Article article = requireArticle(interaction.getArticleId(), relations);
        ArticleLikeVO vo = BeanUtil.copyProperties(article, ArticleLikeVO.class);
        fillArticleRelations(article, vo, relations);
        vo.setId(interaction.getId());
        vo.setArticleId(interaction.getArticleId());
        vo.setArticleCreateAt(article.getCreateAt());
        vo.setArticleUpdateAt(article.getUpdateAt());
        vo.setLikedTime(interaction.getCreatedTime());
        return vo;
    }

    private void fillArticleRelations(Article article, Object vo, Relations relations) {
        User author = relations.users().get(article.getUserId());
        if (author == null) {
            throw notFound(Messages.UNDEFINED_ARTICLE_AUTHOR_ID + article.getUserId());
        }
        SubCategory subCategory = article.getSubCategoryId() == null
                ? null
                : relations.subCategories().get(article.getSubCategoryId().longValue());
        if (subCategory == null) {
            throw notFound(Messages.UNDEFINED_SUB_CATEGORY_AUTHOR_ID + article.getSubCategoryId());
        }
        Category category = relations.categories().get(subCategory.getCategoryId());
        if (category == null) {
            throw notFound(Messages.UNDEFINED_CATEGORY_AUTHOR_ID + subCategory.getCategoryId());
        }
        if (vo instanceof ArticleCollectVO collectVO) {
            collectVO.setAuthorName(author.getName());
            collectVO.setSubCategoryName(subCategory.getName());
            collectVO.setCategoryName(category.getName());
        } else if (vo instanceof ArticleLikeVO likeVO) {
            likeVO.setAuthorName(author.getName());
            likeVO.setSubCategoryName(subCategory.getName());
            likeVO.setCategoryName(category.getName());
        }
    }

    private Article requireArticle(Long articleId, Relations relations) {
        Article article = relations.articles().get(articleId);
        if (article == null) {
            throw notFound(Messages.UNDEFINED_ARTICLE_ID + articleId);
        }
        return article;
    }

    private BusinessException notFound(String message) {
        return BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(message).build();
    }

    private record Relations(
            Map<Long, Article> articles,
            Map<Long, User> users,
            Map<Long, SubCategory> subCategories,
            Map<Long, Category> categories) {
    }
}
