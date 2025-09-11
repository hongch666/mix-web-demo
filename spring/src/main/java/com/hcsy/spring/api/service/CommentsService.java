package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.po.Comments;

public interface CommentsService extends IService<Comments> {
    IPage<Comments> listCommentsWithFilter(Page<Comments> page, CommentsQueryDTO queryDTO);

    IPage<Comments> listCommentsByUserId(Page<Comments> page, Long userId);

    IPage<Comments> listCommentsByArticleId(Page<Comments> page, Long articleId);
}
