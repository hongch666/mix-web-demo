package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.vo.ArticleLikeVO;

public interface ArticleLikeService extends IService<ArticleLike> {

    /**
     * 添加点赞
     */
    boolean addLike(Long articleId, Long userId);

    /**
     * 取消点赞
     */
    boolean removeLike(Long articleId, Long userId);

    /**
     * 检查用户是否点赞了某篇文章
     */
    boolean isLiked(Long articleId, Long userId);

    /**
     * 获取用户的所有点赞（包含文章详情）
     */
    IPage<ArticleLikeVO> listUserLikes(Long userId, Page<ArticleLike> page);

    /**
     * 获取文章的点赞数
     */
    Long getLikeCountByArticleId(Long articleId);
}
