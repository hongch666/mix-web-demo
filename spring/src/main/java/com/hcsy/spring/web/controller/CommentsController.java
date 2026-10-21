package com.hcsy.spring.web.controller;

import java.util.Arrays;
import java.util.List;

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

import com.hcsy.spring.application.service.CommentsService;
import com.hcsy.spring.common.constants.BusinessType;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.ParamSource;
import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.common.constants.SyncResource;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.BatchIdsDTO;
import com.hcsy.spring.entity.dto.CommentCreateDTO;
import com.hcsy.spring.entity.dto.CommentUpdateDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.vo.AICommentsVO;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.CommentSyncVO;
import com.hcsy.spring.entity.vo.CommentsVO;
import com.hcsy.spring.entity.vo.MapDataVO;
import com.hcsy.spring.entity.vo.PageVO;
import com.hcsy.spring.web.logging.annotation.ApiLog;
import com.hcsy.spring.web.security.annotation.RequireInternalToken;
import com.hcsy.spring.web.security.annotation.RequirePermission;
import com.hcsy.spring.web.sync.annotation.DataSync;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 评论控制器，聚合 /comments 下的评论增删改查、普通与AI评论分页条件查询、评论评分统计及同步数据接口
 */
@RestController
@RequestMapping("/comments")
@RequiredArgsConstructor
@Tag(name = "评论模块", description = "文章评论功能相关API，包括评论发布、回复、删除、评论列表查询等")
public class CommentsController {
    private final CommentsService commentsService;

    /**
     * POST /comments 接口，根据创建DTO新增评论并返回新评论ID，文章或用户不存在时返回404
     */
    @PostMapping
    @Operation(summary = "新增评论", description = "通过请求体创建评论信息")
    @DataSync(resource = SyncResource.COMMENTS, changeType = SyncChangeType.INSERT, description = "新增评论后同步图谱与数仓")
    @ApiLog("新增评论")
    public Mono<Result<Long>> createComment(@Valid @RequestBody CommentCreateDTO dto) {
        return commentsService.createComment(dto).map(saved -> Result.success(saved.getId()))
            .defaultIfEmpty(Result.<Long>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_ARTICLE_COMMENT));
    }

    /**
     * PUT /comments 接口，根据更新DTO修改评论内容，需管理员或评论作者本人权限
     */
    @PutMapping
    @Operation(summary = "修改评论", description = "通过请求体修改评论信息")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = BusinessType.COMMENT, paramSource = ParamSource.BODY,
        paramName = "id")
    @DataSync(resource = SyncResource.COMMENTS, changeType = SyncChangeType.UPDATE, description = "修改评论后同步图谱与数仓")
    @ApiLog("修改评论")
    public Mono<Result<Void>> updateComment(@Valid @RequestBody CommentUpdateDTO dto) {
        return commentsService.updateComment(dto)
            .map(ignored -> Result.<Void>success())
            .defaultIfEmpty(Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_ARTICLE_COMMENT));
    }

    /**
     * DELETE /comments/{id} 接口，按ID删除评论，需管理员或评论作者本人权限
     */
    @DeleteMapping("/{id}")
    @Operation(summary = "删除评论", description = "根据id删除评论")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = BusinessType.COMMENT, paramSource = ParamSource.PATH_SINGLE,
        paramName = "id")
    @DataSync(resource = SyncResource.COMMENTS, changeType = SyncChangeType.DELETE, description = "删除评论后同步图谱与数仓")
    @ApiLog("删除评论")
    public Mono<Result<Void>> deleteComment(@PathVariable Long id) {
        return commentsService.deleteComment(id).thenReturn(Result.<Void>success());
    }

    /**
     * DELETE /comments/batch/{ids} 接口，按逗号分隔的ID列表批量删除评论
     */
    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除评论", description = "根据id数组批量删除评论，多个id用英文逗号分隔")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = BusinessType.COMMENT, paramSource = ParamSource.PATH_SINGLE,
        paramName = "ids")
    @DataSync(resource = SyncResource.COMMENTS, changeType = SyncChangeType.DELETE, description = "批量删除评论后同步图谱与数仓")
    @ApiLog("批量删除评论")
    public Mono<Result<Void>> deleteComments(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
            .map(String::trim).filter(value -> !value.isEmpty()).map(Long::valueOf).toList();
        return commentsService.deleteComments(idList).thenReturn(Result.<Void>success());
    }

    /**
     * GET /comments/{id} 接口，按ID返回评论详情，不存在时返回404
     */
    @GetMapping("/{id}")
    @Operation(summary = "根据id查询评论", description = "根据id查询评论")
    @ApiLog("根据id查询评论")
    public Mono<Result<CommentsVO>> getCommentsById(@PathVariable Long id) {
        return commentsService.getCommentDetail(id)
            .map(Result::success)
            .defaultIfEmpty(Result.<CommentsVO>error(HttpCode.NOT_FOUND, Messages.COMMENT_ID + id));
    }

    /**
     * GET /comments 接口，分页返回普通用户评论列表，支持用户名与文章标题模糊筛选，仅管理员可用
     */
    @GetMapping
    @Operation(summary = "获取普通评论信息", description = "分页获取普通评论信息列表，并支持用户名和文章标题模糊查询")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.COMMENT, paramSource = ParamSource.QUERY)
    @ApiLog("获取普通评论信息")
    public Mono<Result<PageVO<CommentsVO>>> listComments(@ParameterObject @ModelAttribute CommentsQueryDTO query) {
        return commentsService.listCommentsWithFilter(query.getPage(), query.getSize(), query)
            .flatMap(commentsService::listCommentDetails)
            .map(Result::success);
    }

    /**
     * GET /comments/ai 接口，分页返回AI评论列表，支持AI类型与文章标题模糊筛选，仅管理员可用
     */
    @GetMapping("/ai")
    @Operation(summary = "获取AI评论信息", description = "分页获取AI评论信息列表，并支持AI类型和文章标题模糊查询")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.COMMENT, paramSource = ParamSource.QUERY)
    @ApiLog("获取AI评论信息")
    public Mono<Result<PageVO<CommentsVO>>> listAIComments(@ParameterObject @ModelAttribute CommentsQueryDTO query) {
        return commentsService.listAICommentsWithFilter(query.getPage(), query.getSize(), query)
            .flatMap(commentsService::listCommentDetails)
            .map(Result::success);
    }

    /**
     * GET /comments/user/{id} 接口，分页返回指定用户发表的评论列表
     */
    @GetMapping("/user/{id}")
    @Operation(summary = "根据用户id分页获取评论", description = "根据用户id分页获取评论")
    @ApiLog("根据用户id分页获取评论")
    public Mono<Result<PageVO<CommentsVO>>> listCommentsByUserId(
        @PathVariable Long id,
        @RequestParam(defaultValue = "10") int size,
        @RequestParam(defaultValue = "1") int page) {
        return commentsService.listCommentsByUserId(page, size, id)
            .flatMap(commentsService::listCommentDetails)
            .map(Result::success);
    }

    /**
     * GET /comments/article/{id} 接口，分页返回指定文章的评论，支持按创建时间或评分排序，排序参数非法时返回400
     */
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
            .flatMap(commentsService::listCommentDetails)
            .map(Result::success);
    }

    /**
     * GET /comments/article/ai/{id} 接口，返回指定文章的全部AI评论列表
     */
    @GetMapping("/article/ai/{id}")
    @Operation(summary = "根据文章id获取AI评论", description = "根据文章id获取AI评论")
    @ApiLog("根据文章id获取AI评论")
    public Mono<Result<List<AICommentsVO>>> listAICommentsByArticleId(@PathVariable Long id) {
        return commentsService.listAICommentDetailsByArticleId(id).map(Result::success);
    }

    /**
     * POST /comments/scores/batch 内部接口，按文章ID列表批量返回评论评分并按用户角色分组
     */
    @PostMapping("/scores/batch")
    @Operation(summary = "批量查询评论评分（内部）", description = "根据文章ID列表批量查询评论评分，按角色分组，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部批量查询评论评分")
    public Mono<Result<List<ArticleCommentScoresVO>>> getCommentScoresByArticleIds(
        @Valid @RequestBody BatchIdsDTO dto) {
        return commentsService.getCommentScoresByArticleIds(dto.getIds())
            .map(Result::success);
    }

    /**
     * POST /comments/batch 内部接口，按ID列表批量返回评论关联关系，供内部服务精确同步 Neo4j
     */
    @PostMapping("/batch")
    @Operation(summary = "批量查询评论（内部）", description = "根据ID列表批量查询评论关联关系，供内部服务精确同步 Neo4j 使用")
    @RequireInternalToken
    @ApiLog("内部批量查询评论")
    public Mono<Result<List<CommentSyncVO>>> getCommentsByIds(@Valid @RequestBody BatchIdsDTO dto) {
        return commentsService.getCommentSyncByIds(dto.getIds()).map(Result::success);
    }

    /**
     * GET /comments/neo4j-sync 内部接口，按 updatedAfter 增量返回评论表数据供 FastAPI 同步 Neo4j
     */
    @GetMapping("/neo4j-sync")
    @Operation(summary = "获取评论表数据用于Neo4j同步（内部）", description = "获取评论表数据，支持增量同步，供FastAPI同步Neo4j使用")
    @RequireInternalToken
    @ApiLog("内部获取Neo4j同步评论数据")
    public Mono<Result<List<CommentSyncVO>>> getNeo4jSyncComments(
        @RequestParam(required = false) String updatedAfter) {
        return commentsService.getNeo4jSyncComments(updatedAfter).map(Result::success);
    }

    /**
     * POST /comments/internal/create 内部接口，直接保存评论实体，供内部服务远程调用
     */
    @PostMapping("/internal/create")
    @Operation(summary = "创建评论（内部）", description = "创建评论，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部创建评论")
    public Mono<Result<Void>> createCommentInternal(@RequestBody Comments comments) {
        return commentsService.save(comments).thenReturn(Result.<Void>success());
    }

    /**
     * GET /comments/statistics/ai-count/{articleId} 内部接口，返回指定文章的AI评论数量
     */
    @GetMapping("/statistics/ai-count/{articleId}")
    @Operation(summary = "获取文章AI评论数（内部）", description = "获取文章的AI评论数，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取文章AI评论数")
    public Mono<Result<Long>> getAiCommentsNumByArticleId(@PathVariable Long articleId) {
        return commentsService.getAiCommentsNumByArticleId(articleId).map(Result::success);
    }

    /**
     * POST /comments/statistics/delete-ai/{articleId} 内部接口，删除指定文章的全部AI评论
     */
    @PostMapping("/statistics/delete-ai/{articleId}")
    @Operation(summary = "删除文章AI评论（内部）", description = "删除文章的AI评论，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部删除文章AI评论")
    public Mono<Result<Void>> deleteAiCommentsByArticleId(@PathVariable Long articleId) {
        return commentsService.deleteAiCommentsByArticleId(articleId).then(Mono.just(Result.success()));
    }

    /**
     * GET /comments/statistics/monthly-trend/{userId} 内部接口，返回指定用户本月的评论趋势统计
     */
    @GetMapping("/statistics/monthly-trend/{userId}")
    @Operation(summary = "获取用户月度评论趋势（内部）", description = "获取用户本月评论的趋势，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部获取用户月度评论趋势")
    public Mono<Result<MapDataVO>> getMonthlyCommentTrend(@PathVariable Long userId) {
        return commentsService.getMonthlyCommentTrend(userId).map(Result::success);
    }

}
