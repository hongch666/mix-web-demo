package com.hcsy.spring.api.controller;

import java.util.ArrayList;
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
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.entity.dto.CommentCreateDTO;
import com.hcsy.spring.entity.dto.CommentUpdateDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.AICommentsVO;
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
    private final ArticleService articleService;
    private final UserService userService;

    // 新增评论
    @PostMapping
    @Operation(summary = "新增评论", description = "通过请求体创建评论信息")
    @ApiLog("新增评论")
    public Result createComment(@Valid @RequestBody CommentCreateDTO commentCreateDTO) {
        Comments comment = BeanUtil.toBean(commentCreateDTO, Comments.class);
        // 获取对应文章id
        Article article = articleService.findByArticleTitle(commentCreateDTO.getArticleTitle());
        if (article == null) {
            return Result.error("文章不存在，无法评论");
        }
        comment.setArticleId(article.getId());
        // 获取对应用户id
        User user = userService.findByUsername(commentCreateDTO.getUsername());
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
    @RequirePermission(roles = {
            "admin" }, allowSelf = true, businessType = "comment", paramSource = "body", paramNames = { "id" })
    @ApiLog("修改评论")
    public Result updateComment(@Valid @RequestBody CommentUpdateDTO commentUpdateDTO) {
        Comments comment = BeanUtil.toBean(commentUpdateDTO, Comments.class);
        // 获取对应文章id
        Article article = articleService.findByArticleTitle(commentUpdateDTO.getArticleTitle());
        if (article == null) {
            return Result.error("文章不存在，无法评论");
        }
        comment.setArticleId(article.getId());
        // 获取对应用户id
        User user = userService.findByUsername(commentUpdateDTO.getUsername());
        if (user == null) {
            return Result.error("用户不存在，无法评论");
        }
        comment.setUserId(user.getId());

        commentsService.updateById(comment);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除评论", description = "根据id删除评论")
    @RequirePermission(roles = {}, allowSelf = true, businessType = "comment", paramSource = "path_multi", paramNames = {
            "comments", "id" })
    @ApiLog("删除评论")
    public Result deleteComment(@PathVariable Long id) {
        commentsService.removeById(id);
        return Result.success();
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除评论", description = "根据id数组批量删除评论，多个id用英文逗号分隔")
    @RequirePermission(roles = {}, allowSelf = true, businessType = "comment", paramSource = "path_multi", paramNames = {
            "comments", "batch", "ids" })
    @ApiLog("批量删除评论")
    public Result deleteComments(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        commentsService.removeByIds(idList);
        return Result.success();
    }

    @GetMapping("/{id}")
    @Operation(summary = "根据id查询评论", description = "根据id查询评论")
    @ApiLog("根据id查询评论")
    public Result getCommentsById(@PathVariable Long id) {
        Comments comments = commentsService.getById(id);
        // 修改返回结果，包含用户名和文章标题
        CommentsVO commentsVO = BeanUtil.copyProperties(comments, CommentsVO.class);
        // 查询用户名
        User user = userService.getById(comments.getUserId());
        commentsVO.setUsername(user != null ? user.getName() : "未知用户");
        commentsVO.setPic(user != null ? user.getImg() : null);
        // 查询文章标题
        Article article = articleService.getById(comments.getArticleId());
        commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
        return Result.success(commentsVO);
    }

    @GetMapping()
    @Operation(summary = "获取普通评论信息", description = "分页获取普通评论信息列表，并支持用户名和文章标题模糊查询")
    @ApiLog("获取普通评论信息")
    public Result listComments(@ModelAttribute CommentsQueryDTO queryDTO) {
        Page<Comments> commentsPage = new Page<>(queryDTO.getPage(), queryDTO.getSize());
        IPage<Comments> resultPage = commentsService.listCommentsWithFilter(commentsPage, queryDTO);
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        // 构建评论视图对象，包含用户名和文章标题
        List<CommentsVO> commentVOs = resultPage.getRecords().stream().map(comment -> {
            CommentsVO commentsVO = BeanUtil.copyProperties(comment, CommentsVO.class);
            // 查询用户名
            User user = userService.getById(comment.getUserId());
            commentsVO.setUsername(user != null ? user.getName() : "未知用户");
            commentsVO.setPic(user != null ? user.getImg() : null);
            // 查询文章标题
            Article article = articleService.getById(comment.getArticleId());
            commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
            return commentsVO;
        }).toList();
        data.put("list", commentVOs);
        return Result.success(data);
    }

    @GetMapping("/ai")
    @Operation(summary = "获取AI评论信息", description = "分页获取AI评论信息列表，并支持AI类型和文章标题模糊查询")
    @ApiLog("获取AI评论信息")
    public Result listAIComments(@ModelAttribute CommentsQueryDTO queryDTO) {
        Page<Comments> commentsPage = new Page<>(queryDTO.getPage(), queryDTO.getSize());
        IPage<Comments> resultPage = commentsService.listAICommentsWithFilter(commentsPage, queryDTO);
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        // 构建AI评论视图对象，包含AI类型和文章标题
        List<CommentsVO> commentVOs = resultPage.getRecords().stream().map(comment -> {
            CommentsVO commentsVO = BeanUtil.copyProperties(comment, CommentsVO.class);
            // 查询AI类型（用户名）
            User user = userService.getById(comment.getUserId());
            commentsVO.setUsername(user != null ? user.getName() : "未知AI");
            commentsVO.setPic(user != null ? user.getImg() : null);
            // 查询文章标题
            Article article = articleService.getById(comment.getArticleId());
            commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
            return commentsVO;
        }).toList();
        data.put("list", commentVOs);
        return Result.success(data);
    }

    // 根据用户id分页获取评论
    @GetMapping("/user/{id}")
    @Operation(summary = "根据用户id分页获取评论", description = "根据用户id分页获取评论")
    @ApiLog("根据用户id分页获取评论")
    public Result listCommentsByUserId(
            @PathVariable Long id,
            @RequestParam(defaultValue = "10", required = false) int size,
            @RequestParam(defaultValue = "1", required = false) int page) {
        Page<Comments> commentsPage = new Page<>(page, size);
        IPage<Comments> resultPage = commentsService.listCommentsByUserId(commentsPage, id);
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        // 构建评论视图对象，包含用户名和文章标题
        List<CommentsVO> commentVOs = resultPage.getRecords().stream().map(comment -> {
            CommentsVO commentsVO = BeanUtil.copyProperties(comment, CommentsVO.class);
            // 查询用户名
            User user = userService.getById(comment.getUserId());
            commentsVO.setUsername(user != null ? user.getName() : "未知用户");
            commentsVO.setPic(user != null ? user.getImg() : null);
            // 查询文章标题
            Article article = articleService.getById(comment.getArticleId());
            commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
            return commentsVO;
        }).toList();
        data.put("list", commentVOs);
        return Result.success(data);
    }

    // 根据文章id分页获取评论
    @GetMapping("/article/{id}")
    @Operation(summary = "根据文章id分页获取评论", description = "根据文章id分页获取评论")
    @ApiLog("根据文章id分页获取评论")
    public Result listCommentsByArticleId(
            @PathVariable Long id,
            @RequestParam(defaultValue = "create_time", required = false) String sortWay,
            @RequestParam(defaultValue = "10", required = false) int size,
            @RequestParam(defaultValue = "1", required = false) int page) {
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
            User user = userService.getById(comment.getUserId());
            commentsVO.setUsername(user != null ? user.getName() : "未知用户");
            commentsVO.setPic(user != null ? user.getImg() : null);
            // 查询文章标题
            Article article = articleService.getById(comment.getArticleId());
            commentsVO.setArticleTitle(article != null ? article.getTitle() : "未知文章");
            return commentsVO;
        }).toList();
        data.put("list", commentVOs);
        return Result.success(data);
    }

    // 根据文章id获取AI评论
    @GetMapping("/article/ai/{id}")
    @Operation(summary = "根据文章id获取AI评论", description = "根据文章id获取AI评论")
    @ApiLog("根据文章id获取AI评论")
    public Result listAICommentsByArticleId(@PathVariable Long id) {
        List<Comments> aiComments = commentsService.listAICommentsByArticleId(id);
        // 构建AI评论视图对象，包含评论内容、星级评分和AI类型
        List<AICommentsVO> data = new ArrayList<>();
        for (Comments comment : aiComments) {
            AICommentsVO aiCommentsVO = BeanUtil.copyProperties(comment, AICommentsVO.class);
            Long userId = comment.getUserId();
            String aiType = userService.getById(userId).getName();
            aiCommentsVO.setAiType(aiType);
            aiCommentsVO.setPic(userService.getById(userId).getImg());
            data.add(aiCommentsVO);
        }
        return Result.success(data);
    }
}