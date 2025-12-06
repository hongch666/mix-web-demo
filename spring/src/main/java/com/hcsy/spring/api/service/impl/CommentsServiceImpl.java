package com.hcsy.spring.api.service.impl;

import java.util.ArrayList;
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
        // 准备查询条件
        String content = (queryDTO.getContent() != null && !queryDTO.getContent().isEmpty())
                ? queryDTO.getContent()
                : null;

        List<Long> articleIds = null;
        // 获取模糊匹配的文章列表，通过id数组构建查询
        if (queryDTO.getArticleTitle() != null && !queryDTO.getArticleTitle().isEmpty()) {
            List<Article> articles = articleService.listAllArticlesByTitle(queryDTO.getArticleTitle());
            articleIds = articles.stream().map(Article::getId).toList();
            if (articleIds.isEmpty()) {
                // 如果没有匹配的文章，直接返回空结果
                return new Page<>(page.getCurrent(), page.getSize(), 0);
            }
        }

        List<Long> userIds = null;
        // 获取模糊匹配的用户列表，通过id数组构建查询
        if (queryDTO.getUsername() != null && !queryDTO.getUsername().isEmpty()) {
            List<User> users = userService.listAllUserByUsername(queryDTO.getUsername());
            userIds = users.stream().map(User::getId).toList();
            if (userIds.isEmpty()) {
                // 如果没有匹配的用户，直接返回空结果
                return new Page<>(page.getCurrent(), page.getSize(), 0);
            }
        }

        // 只查询普通用户（非AI用户）的评论
        List<Long> normalUserIds = userService.list(
                Wrappers.lambdaQuery(User.class).ne(User::getRole, "ai")).stream().map(User::getId).toList();

        if (normalUserIds.isEmpty()) {
            return new Page<>(page.getCurrent(), page.getSize(), 0);
        }

        // 如果指定了用户，则求交集；否则使用所有普通用户
        if (userIds != null) {
            userIds = userIds.stream().filter(normalUserIds::contains).toList();
            if (userIds.isEmpty()) {
                return new Page<>(page.getCurrent(), page.getSize(), 0);
            }
        } else {
            userIds = normalUserIds;
        }

        // 使用SQL级别JOIN查询，只查询普通用户评论
        return this.baseMapper.selectCommentsWithFilter(page, content, articleIds, userIds);
    }

    public IPage<Comments> listAICommentsWithFilter(Page<Comments> page, CommentsQueryDTO queryDTO) {
        // 准备查询条件
        String content = (queryDTO.getContent() != null && !queryDTO.getContent().isEmpty())
                ? queryDTO.getContent()
                : null;

        List<Long> articleIds = null;
        // 获取模糊匹配的文章列表，通过id数组构建查询
        if (queryDTO.getArticleTitle() != null && !queryDTO.getArticleTitle().isEmpty()) {
            List<Article> articles = articleService.listAllArticlesByTitle(queryDTO.getArticleTitle());
            articleIds = articles.stream().map(Article::getId).toList();
            if (articleIds.isEmpty()) {
                // 如果没有匹配的文章，直接返回空结果
                return new Page<>(page.getCurrent(), page.getSize(), 0);
            }
        }

        // 查询所有 AI 用户 ID
        List<Long> aiUserIds = userService.list(
                Wrappers.lambdaQuery(User.class).eq(User::getRole, "ai")).stream().map(User::getId).toList();

        if (aiUserIds.isEmpty()) {
            return new Page<>(page.getCurrent(), page.getSize(), 0);
        }

        List<Long> userIds = null;
        // 获取模糊匹配的用户列表，通过id数组构建查询
        if (queryDTO.getUsername() != null && !queryDTO.getUsername().isEmpty()) {
            List<User> users = userService.listAllUserByUsername(queryDTO.getUsername());
            userIds = users.stream().map(User::getId).toList();
            if (userIds.isEmpty()) {
                // 如果没有匹配的用户，直接返回空结果
                return new Page<>(page.getCurrent(), page.getSize(), 0);
            }
            // 求交集：只保留既是 AI 用户且匹配用户名的用户
            userIds = userIds.stream().filter(aiUserIds::contains).toList();
            if (userIds.isEmpty()) {
                return new Page<>(page.getCurrent(), page.getSize(), 0);
            }
        } else {
            userIds = aiUserIds;
        }

        // 使用SQL级别JOIN查询，只查询 AI 用户评论
        return this.baseMapper.selectCommentsWithFilter(page, content, articleIds, userIds);
    }

    public IPage<Comments> listCommentsByUserId(Page<Comments> page, Long userId) {
        LambdaQueryWrapper<Comments> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Comments::getUserId, userId);
        IPage<Comments> commentsPage = this.page(page, queryWrapper);
        return commentsPage;
    }

    public IPage<Comments> listCommentsByArticleId(Page<Comments> page, Long articleId, String sortWay) {
        // ✨ 使用SQL级别JOIN过滤，确保分页基于已过滤的数据
        // 这样避免了分页不准确的问题（当前面页数中有AI评论时）
        return this.baseMapper.selectCommentsByArticleIdWithoutAI(page, articleId, sortWay);
    }

    public List<Comments> listAICommentsByArticleId(Long articleId) {
        // 查询所有 AI 用户的 ID 列表
        LambdaQueryWrapper<User> userQueryWrapper = Wrappers.lambdaQuery();
        userQueryWrapper.eq(User::getRole, "ai")
                .select(User::getId); // 只查询ID字段以提高性能
        List<User> aiUsers = userService.list(userQueryWrapper);

        // 提取 AI 用户 ID
        List<Long> aiUserIds = aiUsers.stream()
                .map(User::getId)
                .toList();

        // 如果没有 AI 用户，直接返回空列表
        if (aiUserIds.isEmpty()) {
            return new ArrayList<>();
        }

        // 查询当前文章对应的 AI 用户评论列表
        LambdaQueryWrapper<Comments> commentsQueryWrapper = Wrappers.lambdaQuery();
        commentsQueryWrapper.eq(Comments::getArticleId, articleId)
                .in(Comments::getUserId, aiUserIds)
                .orderByDesc(Comments::getCreateTime);

        return this.list(commentsQueryWrapper);
    }
}
