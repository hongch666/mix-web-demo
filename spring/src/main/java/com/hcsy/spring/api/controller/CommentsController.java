package com.hcsy.spring.api.controller;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springdoc.core.annotations.ParameterObject;
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

import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.CommentsService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.core.annotation.RequirePermission;
import com.hcsy.spring.entity.dto.BatchIdsDTO;
import com.hcsy.spring.entity.dto.CommentCreateDTO;
import com.hcsy.spring.entity.dto.CommentUpdateDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.AICommentsVO;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.CommentsVO;
import com.hcsy.spring.entity.vo.MapDataVO;
import com.hcsy.spring.entity.vo.PageVO;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/comments")
@RequiredArgsConstructor
@Tag(name = "评论模块", description = "文章评论功能相关API，包括评论发布、回复、删除、评论列表查询等")
public class CommentsController {
    private final CommentsService commentsService;
    private final ArticleService articleService;
    private final UserService userService;

    @PostMapping
    @Operation(summary = "新增评论", description = "通过请求体创建评论信息")
    @Neo4jSync(description = "新增评论后同步 Neo4j")
    @ApiLog("新增评论")
    public Mono<Result<Void>> createComment(@Valid @RequestBody CommentCreateDTO dto) {
        return Mono.zip(
            articleService.findByArticleTitle(dto.getArticleTitle()),
            userService.findByUsername(dto.getUsername()))
            .flatMap(result -> saveComment(dto, result.getT1(), result.getT2()))
            .defaultIfEmpty(Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_ARTICLE_COMMENT));
    }

    @PutMapping
    @Operation(summary = "修改评论", description = "通过请求体修改评论信息")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = "comment", paramSource = "body", paramNames = { "id" })
    @Neo4jSync(description = "修改评论后同步 Neo4j")
    @ApiLog("修改评论")
    public Mono<Result<Void>> updateComment(@Valid @RequestBody CommentUpdateDTO dto) {
        return Mono.zip(
            articleService.findByArticleTitle(dto.getArticleTitle()),
            userService.findByUsername(dto.getUsername()))
            .flatMap(result -> {
                Comments comment = BeanUtil.toBean(dto, Comments.class);
                comment.setArticleId(result.getT1().getId());
                comment.setUserId(result.getT2().getId());
                return commentsService.update(comment).thenReturn(Result.<Void>success());
            })
            .defaultIfEmpty(Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_ARTICLE_COMMENT));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除评论", description = "根据id删除评论")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = "comment", paramSource = "path_single", paramNames = { "id" })
    @Neo4jSync(description = "删除评论后同步 Neo4j")
    @ApiLog("删除评论")
    public Mono<Result<Void>> deleteComment(@PathVariable Long id) {
        return commentsService.deleteComment(id).thenReturn(Result.<Void>success());
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除评论", description = "根据id数组批量删除评论，多个id用英文逗号分隔")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = "comment", paramSource = "path_single", paramNames = { "ids" })
    @Neo4jSync(description = "批量删除评论后同步 Neo4j")
    @ApiLog("批量删除评论")
    public Mono<Result<Void>> deleteComments(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
            .map(String::trim).filter(value -> !value.isEmpty()).map(Long::valueOf).toList();
        return commentsService.deleteComments(idList).thenReturn(Result.<Void>success());
    }

    @GetMapping("/{id}")
    @Operation(summary = "根据id查询评论", description = "根据id查询评论")
    @ApiLog("根据id查询评论")
    public Mono<Result<CommentsVO>> getCommentsById(@PathVariable Long id) {
        return commentsService.getById(id)
            .flatMap(this::toCommentsVO)
            .map(Result::success)
            .defaultIfEmpty(Result.<CommentsVO>error(HttpCode.NOT_FOUND, Messages.COMMENT_ID + id));
    }

    @GetMapping
    @Operation(summary = "获取普通评论信息", description = "分页获取普通评论信息列表，并支持用户名和文章标题模糊查询")
    @RequirePermission(roles = { "admin" }, businessType = "comment", paramSource = "query", paramNames = { "page",
        "size", "username", "article_title" })
    @ApiLog("获取普通评论信息")
    public Mono<Result<PageVO<CommentsVO>>> listComments(@ParameterObject @ModelAttribute CommentsQueryDTO query) {
        return commentsService.listCommentsWithFilter(query.getPage(), query.getSize(), query)
            .flatMap(this::toCommentsPage)
            .map(Result::success);
    }

    @GetMapping("/ai")
    @Operation(summary = "获取AI评论信息", description = "分页获取AI评论信息列表，并支持AI类型和文章标题模糊查询")
    @RequirePermission(roles = { "admin" }, businessType = "comment", paramSource = "query", paramNames = { "page",
        "size", "ai_type", "article_title" })
    @ApiLog("获取AI评论信息")
    public Mono<Result<PageVO<CommentsVO>>> listAIComments(@ParameterObject @ModelAttribute CommentsQueryDTO query) {
        return commentsService.listAICommentsWithFilter(query.getPage(), query.getSize(), query)
            .flatMap(this::toCommentsPage)
            .map(Result::success);
    }

    @GetMapping("/user/{id}")
    @Operation(summary = "根据用户id分页获取评论", description = "根据用户id分页获取评论")
    @ApiLog("根据用户id分页获取评论")
    public Mono<Result<PageVO<CommentsVO>>> listCommentsByUserId(
        @PathVariable Long id,
        @RequestParam(defaultValue = "10") int size,
        @RequestParam(defaultValue = "1") int page) {
        return commentsService.listCommentsByUserId(page, size, id)
            .flatMap(this::toCommentsPage)
            .map(Result::success);
    }

    @GetMapping("/article/{id}")
    @Operation(summary = "根据文章id分页获取评论", description = "根据文章id分页获取评论")
    @ApiLog("根据文章id分页获取评论")
    public Mono<Result<PageVO<CommentsVO>>> listCommentsByArticleId(
        @PathVariable Long id,
        @RequestParam(defaultValue = "create_time") String sortWay,
        @RequestParam(defaultValue = "10") int size,
        @RequestParam(defaultValue = "1") int page) {
        if (!"create_time".equals(sortWay) && !"star".equals(sortWay)) {
            return Mono.just(Result.error(HttpCode.BAD_REQUEST, Messages.SORT_WAY + sortWay));
        }
        return commentsService.listCommentsByArticleId(page, size, id, sortWay)
            .flatMap(this::toCommentsPage)
            .map(Result::success);
    }

    @GetMapping("/article/ai/{id}")
    @Operation(summary = "根据文章id获取AI评论", description = "根据文章id获取AI评论")
    @ApiLog("根据文章id获取AI评论")
    public Mono<Result<List<AICommentsVO>>> listAICommentsByArticleId(@PathVariable Long id) {
        return commentsService.listAICommentsByArticleId(id)
            .collectList()
            .flatMap(comments -> {
                Set<Long> userIds = comments.stream().map(Comments::getUserId).collect(Collectors.toSet());
                return userService.listByIds(userIds).collectMap(User::getId, Function.identity())
                    .map(users -> comments.stream().map(comment -> {
                        AICommentsVO vo = BeanUtil.copyProperties(comment, AICommentsVO.class);
                        User user = users.get(comment.getUserId());
                        vo.setAiType(user == null ? Defaults.DEFAULT_AI : user.getName());
                        vo.setPic(user == null ? null : user.getImg());
                        return vo;
                    }).toList());
            })
            .map(Result::success);
    }

    @PostMapping("/scores/batch")
    @Operation(summary = "批量查询评论评分（内部）", description = "根据文章ID列表批量查询评论评分，按角色分组，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部批量查询评论评分")
    public Mono<Result<List<ArticleCommentScoresVO>>> getCommentScoresByArticleIds(
        @Valid @RequestBody BatchIdsDTO dto) {
        return commentsService.getCommentScoresByArticleIds(dto.getIds())
            .map(Result::success);
    }

    @GetMapping("/neo4j-sync")
    @Operation(summary = "获取评论表数据用于Neo4j同步（内部）", description = "获取评论表数据，支持增量同步，供FastAPI同步Neo4j使用")
    @RequireInternalToken
    @ApiLog("内部获取Neo4j同步评论数据")
    public Mono<Result<List<Map<String, Object>>>> getNeo4jSyncComments(
        @RequestParam(required = false) String updatedAfter) {
        return commentsService.getNeo4jSyncComments(updatedAfter).map(Result::success);
    }

    private Mono<Result<Void>> saveComment(CommentCreateDTO dto, Article article, User user) {
        Comments comment = BeanUtil.toBean(dto, Comments.class);
        comment.setArticleId(article.getId());
        comment.setUserId(user.getId());
        return commentsService.save(comment).thenReturn(Result.<Void>success());
    }

    private Mono<CommentsVO> toCommentsVO(Comments comment) {
        Mono<User> user = userService.getById(comment.getUserId()).defaultIfEmpty(new User());
        Mono<Article> article = articleService.getById(comment.getArticleId()).defaultIfEmpty(new Article());
        return Mono.zip(user, article).map(relations -> mapComment(comment, relations.getT1(), relations.getT2()));
    }

    private Mono<PageVO<CommentsVO>> toCommentsPage(PageDTO<Comments> source) {
        Set<Long> userIds = source.getRecords().stream().map(Comments::getUserId).collect(Collectors.toSet());
        Set<Long> articleIds = source.getRecords().stream().map(Comments::getArticleId).collect(Collectors.toSet());
        Mono<Map<Long, User>> users = userService.listByIds(userIds).collectMap(User::getId, Function.identity());
        Mono<Map<Long, Article>> articles = articleService.listByIds(articleIds)
            .collectMap(Article::getId, Function.identity());
        return Mono.zip(users, articles).map(relations -> {
            List<CommentsVO> records = source.getRecords().stream()
                .map(comment -> mapComment(comment, relations.getT1().get(comment.getUserId()),
                    relations.getT2().get(comment.getArticleId())))
                .toList();
            return new PageVO<>(source.getTotal(), records);
        });
    }

    private CommentsVO mapComment(Comments comment, User user, Article article) {
        CommentsVO vo = BeanUtil.copyProperties(comment, CommentsVO.class);
        vo.setUsername(user == null || user.getName() == null ? Defaults.DEFAULT_USER : user.getName());
        vo.setPic(user == null ? null : user.getImg());
        vo.setArticleTitle(
            article == null || article.getTitle() == null ? Defaults.DEFAULT_ARTICLE : article.getTitle());
        return vo;
    }

    // ==================== 内部接口 ====================

    @PostMapping("/internal/create")
    @Operation(summary = "创建评论（内部）", description = "创建评论，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部创建评论")
    public Mono<Result<Comments>> createCommentInternal(@RequestBody Comments comments) {
        return commentsService.save(comments).map(Result::success);
    }

    // ==================== 统计接口 ====================

    @GetMapping("/statistics/ai-count/{articleId}")
    @Operation(summary = "获取文章AI评论数（内部）", description = "获取文章的AI评论数，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取文章AI评论数")
    public Mono<Result<Long>> getAiCommentsNumByArticleId(@PathVariable Long articleId) {
        return commentsService.getAiCommentsNumByArticleId(articleId).map(Result::success);
    }

    @PostMapping("/statistics/delete-ai/{articleId}")
    @Operation(summary = "删除文章AI评论（内部）", description = "删除文章的AI评论，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部删除文章AI评论")
    public Mono<Result<Void>> deleteAiCommentsByArticleId(@PathVariable Long articleId) {
        return commentsService.deleteAiCommentsByArticleId(articleId).then(Mono.just(Result.success()));
    }

    @GetMapping("/statistics/monthly-trend/{userId}")
    @Operation(summary = "获取用户月度评论趋势（内部）", description = "获取用户本月评论的趋势，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取用户月度评论趋势")
    public Mono<Result<MapDataVO>> getMonthlyCommentTrend(@PathVariable Long userId) {
        return commentsService.getMonthlyCommentTrend(userId).map(Result::success);
    }
}
