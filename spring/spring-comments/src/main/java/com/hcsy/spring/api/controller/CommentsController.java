package com.hcsy.spring.api.controller;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.common.client.ArticleClient;
import com.hcsy.spring.common.client.UserClient;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.dto.CommentCreateDTO;
import com.hcsy.spring.entity.dto.CommentUpdateDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.CommentsVO;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/comments")
@RequiredArgsConstructor
@Tag(name = "评论模块", description = "评论相关接口")
public class CommentsController {
    private final CommentsService commentsService;
    private final ArticleClient articleClient;
    private final UserClient userClient;
    private final SimpleLogger logger;

    // 新增评论
    @PostMapping
    @Operation(summary = "新增评论", description = "通过请求体创建评论信息")
    public Result createComment(@Valid @RequestBody CommentCreateDTO commentCreateDTO) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " POST /comments: " + "新增评论\nCommentCreateDTO: %s",
                commentCreateDTO);
        Comments comment = BeanUtil.toBean(commentCreateDTO, Comments.class);
        // 获取对应文章id
        Result articleResult = articleClient.findByArticleTitle(commentCreateDTO.getArticleTitle());
        Article article = BeanUtil.toBean((Map<?, ?>) articleResult.getData(), Article.class);

        if (article == null) {
            return Result.error("文章不存在，无法评论");
        }
        comment.setArticleId(article.getId());
        // 获取对应用户id
        Result userResult = userClient.findByUsername(commentCreateDTO.getUsername());
        User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
        if (user == null) {
            return Result.error("用户不存在，无法评论");
        }
        comment.setUserId(user.getId());
        commentsService.save(comment);

        return Result.success();
    }

    // 修改评论
    @PutMapping
    @Operation(summary = "修改评论", description = "通过请求体修改评论信息")
    @RequirePermission(roles = { "admin" }, allowSelf = true, targetUserIdParam = "commentUpdateDTO")
    public Result updateComment(@Valid @RequestBody CommentUpdateDTO commentUpdateDTO) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " PUT /comments: " + "修改评论\nCommentUpdateDTO: %s",
                commentUpdateDTO);
        Comments comment = BeanUtil.toBean(commentUpdateDTO, Comments.class);
        // 获取对应文章id
        Result articleResult = articleClient.findByArticleTitle(commentUpdateDTO.getArticleTitle());
        Article article = BeanUtil.toBean((Map<?, ?>) articleResult.getData(), Article.class);
        if (article == null) {
            return Result.error("文章不存在，无法评论");
        }
        comment.setArticleId(article.getId());
        // 获取对应用户id
        Result userResult = userClient.findByUsername(commentUpdateDTO.getUsername());
        User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
        if (user == null) {
            return Result.error("用户不存在，无法评论");
        }
        comment.setUserId(user.getId());

        commentsService.updateById(comment);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除评论", description = "根据id删除评论")
    @RequirePermission(roles = { "admin" }, allowSelf = true)
    public Result deleteComment(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " DELETE /comments/{id}: " + "删除评论，ID: %s", id);
        commentsService.removeById(id);
        return Result.success();
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除评论", description = "根据id数组批量删除评论，多个id用英文逗号分隔")
    @RequirePermission(roles = { "admin" }, allowSelf = true)
    public Result deleteComments(@PathVariable String ids) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        logger.info("用户" + userId + ":" + userName + " DELETE /comments/batch/{ids}: " + "批量删除评论，IDS: %s", idList);
        commentsService.removeByIds(idList);
        return Result.success();
    }

    @GetMapping("/{id}")
    @Operation(summary = "根据id查询评论", description = "根据id查询评论")
    public Result getCommentsById(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /comments/{id}: " + "查询评论，ID: %s", id);
        Comments comments = commentsService.getById(id);
        // 修改返回结果，包含用户名和文章标题
        CommentsVO commentsVO = BeanUtil.copyProperties(comments, CommentsVO.class);
        // 查询用户名
        Result userResult = userClient.getById(comments.getUserId());
        User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
        commentsVO.setUsername(user != null ? user.getName() : "未知用户");
        // 查询文章标题
        Result articleResult = articleClient.getById(comments.getArticleId());
        Article article = BeanUtil.toBean((Map<?, ?>) articleResult.getData(), Article.class);

        commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
        return Result.success(commentsVO);
    }

    @GetMapping()
    @Operation(summary = "获取评论信息", description = "分页获取评论信息列表，并支持用户名和文章标题模糊查询")
    public Result listComments(@ModelAttribute CommentsQueryDTO queryDTO) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /comments: " + "获取评论信息\nCommentsQueryDTO: %s", queryDTO);
        Page<Comments> commentsPage = new Page<>(queryDTO.getPage(), queryDTO.getSize());
        IPage<Comments> resultPage = commentsService.listCommentsWithFilter(commentsPage, queryDTO);
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        // 构建评论视图对象，包含用户名和文章标题
        List<CommentsVO> commentVOs = resultPage.getRecords().stream().map(comment -> {
            CommentsVO commentsVO = BeanUtil.copyProperties(comment, CommentsVO.class);
            // 查询用户名
            Result userResult = userClient.getById(comment.getUserId());
            User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
            commentsVO.setUsername(user != null ? user.getName() : "未知用户");
            // 查询文章标题
            Result articleResult = articleClient.getById(comment.getArticleId());
            Article article = BeanUtil.toBean((Map<?, ?>) articleResult.getData(), Article.class);

            commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
            return commentsVO;
        }).toList();
        data.put("list", commentVOs);
        return Result.success(data);
    }

    // 根据用户id分页获取评论
    @GetMapping("/user/{id}")
    @Operation(summary = "根据用户id分页获取评论", description = "根据用户id分页获取评论")
    public Result listCommentsByUserId(
            @PathVariable Long id,
            @RequestParam(defaultValue = "10", required = false) int size,
            @RequestParam(defaultValue = "1", required = false) int page) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /comments/user/{id}: "
                + "根据用户id分页获取评论\nID: %s, PageSize: %d, PageNum: %d", id, size, page);
        Page<Comments> commentsPage = new Page<>(page, size);
        IPage<Comments> resultPage = commentsService.listCommentsByUserId(commentsPage, id);
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        // 构建评论视图对象，包含用户名和文章标题
        List<CommentsVO> commentVOs = resultPage.getRecords().stream().map(comment -> {
            CommentsVO commentsVO = BeanUtil.copyProperties(comment, CommentsVO.class);
            // 查询用户名
            Result userResult = userClient.getById(comment.getUserId());
            User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
            commentsVO.setUsername(user != null ? user.getName() : "未知用户");
            // 查询文章标题
            Result articleResult = articleClient.getById(comment.getArticleId());
            Article article = BeanUtil.toBean((Map<?, ?>) articleResult.getData(), Article.class);
            commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
            return commentsVO;
        }).toList();
        data.put("list", commentVOs);
        return Result.success(data);
    }

    // 根据文章id分页获取评论
    @GetMapping("/article/{id}")
    @Operation(summary = "根据文章id分页获取评论", description = "根据文章id分页获取评论")
    public Result listCommentsByArticleId(
            @PathVariable Long id,
            @RequestParam(defaultValue = "create_time", required = false) String sortWay,
            @RequestParam(defaultValue = "10", required = false) int size,
            @RequestParam(defaultValue = "1", required = false) int page) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /comments/article/{id}: "
                + "根据文章id分页获取评论\nID: %s, PageSize: %d, PageNum: %d", id, size, page);
        // 获取并校验排序方式参数
        if (!sortWay.equals("create_time") && !sortWay.equals("star")) {
            return Result.error("不支持的排序方式: " + sortWay);
        }
        Page<Comments> commentsPage = new Page<>(page, size);
        IPage<Comments> resultPage = commentsService.listCommentsByArticleId(commentsPage, id, sortWay);
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        // 构建评论视图对象，包含用户名和文章标题
        List<CommentsVO> commentVOs = resultPage.getRecords().stream().map(comment -> {
            CommentsVO commentsVO = BeanUtil.copyProperties(comment, CommentsVO.class);
            // 查询用户名
            Result userResult = userClient.getById(comment.getUserId());
            User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
            commentsVO.setUsername(user != null ? user.getName() : "未知用户");
            // 查询文章标题
            Result articleResult = articleClient.getById(comment.getArticleId());
            Article article = BeanUtil.toBean((Map<?, ?>) articleResult.getData(), Article.class);
            commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
            return commentsVO;
        }).toList();
        data.put("list", commentVOs);
        return Result.success(data);
    }
}