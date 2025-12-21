package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.vo.ArticleCollectVO;

public interface ArticleCollectService extends IService<ArticleCollect> {

    /**
     * 添加收藏
     */
    boolean addCollect(Long articleId, Long userId);

    /**
     * 取消收藏
     */
    boolean removeCollect(Long articleId, Long userId);

    /**
     * 检查用户是否收藏了某篇文章
     */
    boolean isCollected(Long articleId, Long userId);

    /**
     * 获取用户的所有收藏（包含文章详情）
     */
    IPage<ArticleCollectVO> listUserCollects(Long userId, Page<ArticleCollect> page);

    /**
     * 获取文章的收藏数
     */
    Long getCollectCountByArticleId(Long articleId);
}
