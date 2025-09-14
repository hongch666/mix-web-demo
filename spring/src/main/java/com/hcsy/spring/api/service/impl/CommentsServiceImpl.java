package com.hcsy.spring.api.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.CommentsMapper;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.po.Comments;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class CommentsServiceImpl extends ServiceImpl<CommentsMapper, Comments> implements CommentsService {
    private final ArticleService articleService;
    private final UserService userService;

    public IPage<Comments> listCommentsWithFilter(Page<Comments> page, CommentsQueryDTO queryDTO) {
        LambdaQueryWrapper<Comments> queryWrapper = Wrappers.lambdaQuery();
        if (queryDTO.getContent() != null && !queryDTO.getContent().isEmpty()) {
            queryWrapper.like(Comments::getContent, queryDTO.getContent()); // 内容模糊匹配
        }
        // 获取模糊匹配的文章列表，通过id数组构建查询
        if (queryDTO.getArticleTitle() != null && !queryDTO.getArticleTitle().isEmpty()) {
            // 模糊查询文章标题，获取对应文章id列表
            List<Article> articles = articleService.listAllArticlesByTitle(queryDTO.getArticleTitle());
            List<Long> articleIds = articles.stream().map(Article::getId).toList();
            if (!articleIds.isEmpty()) {
                queryWrapper.in(Comments::getArticleId, articleIds);
            } else {
                // 如果没有匹配的文章，直接返回空结果
                return new Page<>(page.getCurrent(), page.getSize(), 0);
            }
        }
        // 获取模糊匹配的用户列表，通过id数组构建查询
        if (queryDTO.getUsername() != null && !queryDTO.getUsername().isEmpty()) {
            // 模糊查询用户名，获取对应用户id列表
            List<User> users = userService.listAllUserByUsername(queryDTO.getUsername());
            List<Long> userIds = users.stream().map(User::getId).toList();
            if (!userIds.isEmpty()) {
                queryWrapper.in(Comments::getUserId, userIds);
            } else {
                // 如果没有匹配的用户，直接返回空结果
                return new Page<>(page.getCurrent(), page.getSize(), 0);
            }
        }
        IPage<Comments> commentsPage = this.page(page, queryWrapper);
        return commentsPage;
    }

    public IPage<Comments> listCommentsByUserId(Page<Comments> page, Long userId) {
        LambdaQueryWrapper<Comments> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Comments::getUserId, userId);
        IPage<Comments> commentsPage = this.page(page, queryWrapper);
        return commentsPage;
    }

    public IPage<Comments> listCommentsByArticleId(Page<Comments> page, Long articleId, String sortWay) {
        LambdaQueryWrapper<Comments> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Comments::getArticleId, articleId);
        if (sortWay.equals("star")) {
            queryWrapper.orderByDesc(Comments::getStar);
        } else {
            queryWrapper.orderByDesc(Comments::getCreateTime);
        }
        IPage<Comments> commentsPage = this.page(page, queryWrapper);
        return commentsPage;
    }
}
