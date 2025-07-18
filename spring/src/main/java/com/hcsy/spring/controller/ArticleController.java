package com.hcsy.spring.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.dto.ArticleCreateDTO;
import com.hcsy.spring.dto.ArticleUpdateDTO;
import com.hcsy.spring.po.Article;
import com.hcsy.spring.po.Result;
import com.hcsy.spring.po.User;
import com.hcsy.spring.service.ArticleService;
import com.hcsy.spring.service.UserService;
import com.hcsy.spring.utils.SimpleLogger;
import com.hcsy.spring.utils.UserContext;
import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.util.HashMap;
import java.util.Map;
import java.util.Arrays;
import java.util.List;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/articles")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "文章模块", description = "文章相关接口")
public class ArticleController {

    private final ArticleService articleService;
    private final SimpleLogger logger;
    private final UserService userService;

    @PostMapping
    @Operation(summary = "创建文章", description = "通过请求体创建一篇新文章")
    public Result createArticle(@Valid @RequestBody ArticleCreateDTO dto) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " POST /articles: " + "创建文章\nArticleCreateDTO: %s", dto);
        Article article = BeanUtil.copyProperties(dto, Article.class);
        // 获取用户id
        User user = userService.findByUsername(dto.getUsername());
        if (user == null) {
            return Result.error("用户不存在");
        }
        article.setUserId(user.getId());
        article.setViews(0);
        articleService.saveArticle(article);
        return Result.success();
    }

    @GetMapping("/list")
    @Operation(summary = "获取文章列表", description = "返回所有已发布的文章")
    public Result getPublishedArticles(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /articles/list: " + "获取已发布文章列表\npage: %s, size: %s", page,
                size);
        Page<Article> articlePage = new Page<>(page, size);
        IPage<Article> resultPage = articleService.listPublishedArticles(articlePage);

        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        data.put("list", resultPage.getRecords());
        return Result.success(data);
    }

    @GetMapping("user/{id}")
    @Operation(summary = "获取用户所有文章", description = "返回用户所有文章")
    public Result getPublishedArticles(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @PathVariable Integer id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /articles/user/{id}: "
                + "获取用户所有文章\npage: %s, size: %s, userId: %s", page, size, id);
        Page<Article> articlePage = new Page<>(page, size);
        IPage<Article> resultPage = articleService.listArticlesById(articlePage, id);

        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        data.put("list", resultPage.getRecords());
        return Result.success(data);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取文章详情", description = "根据ID获取文章详情")
    public Result getArticleById(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " GET /articles/{id}: " + "获取文章详情\nID: %s", id);
        Article article = articleService.getById(id);
        if (article == null) {
            return Result.error("文章不存在");
        }
        // 查询作者用户名
        com.hcsy.spring.po.User user = userService.getById(article.getUserId());
        String username = user != null ? user.getName() : null;
        Map<String, Object> data = new HashMap<>();
        data.put("id", article.getId());
        data.put("title", article.getTitle());
        data.put("content", article.getContent());
        data.put("userId", article.getUserId());
        data.put("tags", article.getTags());
        data.put("status", article.getStatus());
        data.put("createAt", article.getCreateAt());
        data.put("updateAt", article.getUpdateAt());
        data.put("views", article.getViews());
        data.put("username", username);
        return Result.success(data);
    }

    @PutMapping
    @Operation(summary = "更新文章", description = "根据DTO更新文章信息")
    public Result updateArticle(@Valid @RequestBody ArticleUpdateDTO dto) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " PUT /articles: " + "更新文章\nArticleUpdateDTO: %s", dto);

        // 获取用户id
        User userFromUsername = userService.findByUsername(dto.getUsername());
        if (userFromUsername == null) {
            return Result.error("用户不存在");
        }

        Article article = BeanUtil.copyProperties(dto, Article.class);
        article.setUserId(userFromUsername.getId());
        Article dbArticle = articleService.getById(dto.getId());
        User user = userService.getById(userId);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        System.out.println("!!-------------------------------!!");
        System.out.println(user.getRole());
        System.out.println("!!-------------------------------!!");
        if (!"admin".equals(user.getRole()) && !userId.equals(dbArticle.getUserId())) {
            System.out.println("hihihi");
            throw new RuntimeException("无权修改他人文章");
        }
        articleService.updateArticle(article);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除文章", description = "根据ID删除文章")
    public Result deleteArticle(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " DELETE /articles/{id}: " + "删除文章\nID: %s", id);
        Article dbArticle = articleService.getById(id);
        User user = userService.getById(userId);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!"admin".equals(user.getRole()) && !userId.equals(dbArticle.getUserId())) {
            throw new RuntimeException("无权删除他人文章");
        }
        articleService.deleteArticle(id);
        return Result.success();
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除文章", description = "根据ID数组批量删除文章，多个ID用英文逗号分隔")
    public Result deleteArticles(@PathVariable String ids) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        logger.info("用户" + userId + ":" + userName + " DELETE /articles/batch/{ids}: " + "批量删除文章，IDS: %s", idList);

        User user = userService.getById(userId);
        for (Long id : idList) {
            Article dbArticle = articleService.getById(id);
            if (dbArticle == null) {
                throw new RuntimeException("文章不存在");
            }
            if (!"admin".equals(user.getRole()) && !userId.equals(dbArticle.getUserId())) {
                throw new RuntimeException("无权删除他人文章");
            }
        }

        articleService.deleteArticles(idList);
        return Result.success();

    }

    @PutMapping("/publish/{id}")
    @Operation(summary = "发布文章", description = "将文章状态修改为发布")
    public Result publishArticle(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " PUT /articles/publish/{id}: " + "发布文章\nID: %s", id);
        articleService.publishArticle(id);
        return Result.success();
    }

    @PutMapping("/view/{id}")
    @Operation(summary = "增加文章阅读量", description = "增加文章阅读量")
    public Result addViewArticle(@PathVariable Long id) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " PUT /articles/view/{id}: " + "增加文章阅读量\nID: %s", id);
        Article dbArticle = articleService.getById(id);
        User user = userService.getById(userId);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!"admin".equals(user.getRole()) && !userId.equals(dbArticle.getUserId())) {
            throw new RuntimeException("无权发布他人文章");
        }
        articleService.addViewArticle(id);
        return Result.success();
    }

}
