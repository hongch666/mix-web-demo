package com.hcsy.spring.api.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.entity.dto.ArticleCreateDTO;
import com.hcsy.spring.entity.dto.ArticleUpdateDTO;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.common.client.CategoryClient;
import com.hcsy.spring.common.client.UserClient;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.UserContext;

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
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;

import com.hcsy.spring.entity.vo.ArticleVO;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@RestController
@RequestMapping("/articles")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "文章模块", description = "文章相关接口")
public class ArticleController {

    private final ArticleService articleService;
    private final SimpleLogger logger;
    private final UserClient userClient;
    private final CategoryClient categoryClient;

    @PostMapping
    @Operation(summary = "创建文章", description = "通过请求体创建一篇新文章")
    public Result createArticle(@Valid @RequestBody ArticleCreateDTO dto) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " POST /articles: " + "创建文章\nArticleCreateDTO: %s", dto);
        Article article = BeanUtil.copyProperties(dto, Article.class);
        // 获取用户id
        Result userResult = userClient.getUserByUsername(dto.getUsername());
        User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
        if (user == null) {
            return Result.error("用户不存在");
        }
        article.setUserId(user.getId());
        article.setViews(0);
        articleService.saveArticle(article);
        return Result.success();
    }

    @GetMapping("/list")
    @Operation(summary = "获取文章列表", description = "返回所有已发布的文章，可根据标题模糊查询")
    public Result getPublishedArticles(
            @RequestParam(required = false) Integer page,
            @RequestParam(required = false) Integer size,
            @RequestParam(required = false) String title) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info(
                "用户" + userId + ":" + userName + " GET /articles/list: " + "获取已发布文章列表\npage: %s, size: %s, title: %s",
                page,
                size, title);

        List<Article> articles;
        long total;
        if (page == null || size == null) {
            // 不分页，查全部
            articles = articleService.listPublishedArticlesByTitle(title);
            total = articles.size();
        } else {
            Page<Article> articlePage = new Page<>(page, size);
            IPage<Article> resultPage = articleService.listPublishedArticlesByTitle(articlePage, title);
            articles = resultPage.getRecords();
            total = resultPage.getTotal();
        }

        // 格式化时间并转为VO
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        List<ArticleVO> voList = articles.stream().map(article -> {
            ArticleVO vo = BeanUtil.copyProperties(article, ArticleVO.class);
            vo.setCreateAt(article.getCreateAt() != null ? article.getCreateAt().format(formatter) : null);
            vo.setUpdateAt(article.getUpdateAt() != null ? article.getUpdateAt().format(formatter) : null);
            return vo;
        }).toList();
        Map<String, Object> data = new HashMap<>();
        data.put("total", total);
        data.put("list", voList);
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

        List<Article> records = resultPage.getRecords();
        List<ArticleWithCategoryVO> voList = new ArrayList<>();
        for (Article article : records) {
            if (article.getSubCategoryId() == null) {
                return Result.error("子分类ID不能为空");
            }

            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);

            // 查询作者用户名
            Long new_id = Long.valueOf(id);
            Result userResult = userClient.getUserById(new_id);
            User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
            vo.setUsername(user != null ? user.getName() : "");
            // 查询子分类信息
            Result subCategoryResult = categoryClient.getSingleSubCategoryById(article.getSubCategoryId());
            SubCategory subCategory = BeanUtil.toBean((Map<?, ?>) subCategoryResult.getData(), SubCategory.class);
            vo.setSubCategoryName(subCategory.getName());
            // 查询主分类信息
            Result categoryResult = categoryClient.getSingleCategoryById(subCategory.getCategoryId());
            Category category = BeanUtil.toBean((Map<?, ?>) categoryResult.getData(), Category.class);
            vo.setCategoryName(category.getName());
            vo.setCategoryId(category.getId());

            voList.add(vo);
        }
        Map<String, Object> data = new HashMap<>();
        data.put("total", resultPage.getTotal());
        data.put("list", voList);
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
        ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);
        // 查询作者用户名
        Result userResult = userClient.getUserById(article.getUserId());
        User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
        String username = user != null ? user.getName() : null;
        vo.setUsername(username);

        return Result.success(vo);
    }

    @PutMapping
    @Operation(summary = "更新文章", description = "根据DTO更新文章信息")
    public Result updateArticle(@Valid @RequestBody ArticleUpdateDTO dto) {
        Long userId = UserContext.getUserId();
        String userName = UserContext.getUsername();
        logger.info("用户" + userId + ":" + userName + " PUT /articles: " + "更新文章\nArticleUpdateDTO: %s", dto);

        // 获取用户id
        Result userNameResult = userClient.getUserByUsername(dto.getUsername());
        User userFromUsername = BeanUtil.toBean((Map<?, ?>) userNameResult.getData(), User.class);
        if (userFromUsername == null) {
            return Result.error("用户不存在");
        }

        Article article = BeanUtil.copyProperties(dto, Article.class);
        article.setUserId(userFromUsername.getId());
        Article dbArticle = articleService.getById(dto.getId());
        Result userResult = userClient.getUserById(userId);
        User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!"admin".equals(user.getRole()) && !userId.equals(dbArticle.getUserId())) {
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
        Result userResult = userClient.getUserById(userId);
        User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
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

        Result userResult = userClient.getUserById(userId);
        User user = BeanUtil.toBean((Map<?, ?>) userResult.getData(), User.class);
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
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        articleService.addViewArticle(id);
        return Result.success();
    }

    @GetMapping("/comment-use/{id}")
    public Result getById(@PathVariable Long id) {
        return Result.success(articleService.getById(id));
    }

    @GetMapping("/comment-use/title/{title}")
    public Result getByTitle(@PathVariable String title) {
        return Result.success(articleService.findByArticleTitle(title));
    }

    @GetMapping("/comment-use/all/{title}")
    public Result getAllByTitle(@PathVariable String title) {
        return Result.success(articleService.listAllArticlesByTitle(title));
    }

}
