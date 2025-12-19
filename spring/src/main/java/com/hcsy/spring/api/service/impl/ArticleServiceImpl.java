package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.ArticleMapper;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import cn.hutool.core.bean.BeanUtil;
import com.hcsy.spring.common.annotation.ArticleSync;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.User;

import lombok.RequiredArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements ArticleService {
    private final ArticleMapper articleMapper;
    private final UserService userService;
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;

    @Override
    @Transactional
    public List<Article> listPublishedArticles() {
        return lambdaQuery()
                .eq(Article::getStatus, 1)
                .list();
    }

    @Override
    @Transactional
    public IPage<Article> listPublishedArticles(Page<Article> page) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getStatus, 1); // 只查已发布
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    @Transactional
    public IPage<Article> listArticlesById(Page<Article> page, Integer id) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getUserId, id);
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    @Transactional
    @ArticleSync(action = "add", description = "创建了1篇文章")
    public boolean saveArticle(Article article) {
        articleMapper.insert(article);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "edit", description = "编辑了1篇文章")
    public boolean updateArticle(Article article) {
        // 校验用户
        Long currentUserId = UserContext.getUserId();
        if (currentUserId == null) {
            throw new RuntimeException("未登录，无法更新文章");
        }

        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(article.getId());
        User user = userService.getById(currentUserId);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!"admin".equals(user.getRole()) && !currentUserId.equals(dbArticle.getUserId())) {
            throw new RuntimeException("无权修改他人文章");
        }
        // 执行修改
        articleMapper.updateById(article);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "delete", description = "删除了1篇文章")
    public boolean deleteArticle(Long id) {
        // 校验用户
        Long currentUserId = UserContext.getUserId();
        if (currentUserId == null) {
            throw new RuntimeException("未登录，无法更新文章");
        }

        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        User user = userService.getById(currentUserId);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (!"admin".equals(user.getRole()) && !currentUserId.equals(dbArticle.getUserId())) {
            throw new RuntimeException("无权删除他人文章");
        }
        // 执行删除
        articleMapper.deleteById(id);
        return true;
    }

    @Transactional
    @ArticleSync(action = "delete", description = "批量删除了")
    public boolean deleteArticles(List<Long> ids) {
        Long currentUserId = UserContext.getUserId();
        if (currentUserId == null) {
            throw new RuntimeException("未登录，无法删除文章");
        }
        for (Long id : ids) {
            Article dbArticle = articleMapper.selectById(id);
            User user = userService.getById(currentUserId);
            if (dbArticle == null) {
                throw new RuntimeException("文章不存在，ID:" + id);
            }
            if (!"admin".equals(user.getRole()) && !currentUserId.equals(dbArticle.getUserId())) {
                throw new RuntimeException("无权删除他人文章，ID:" + id);
            }
        }
        articleMapper.deleteBatchIds(ids);
        return true;
    }

    @Override
    @ArticleSync(action = "publish", description = "发布了1篇文章")
    public void publishArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }

        // 执行发布
        Article article = new Article();
        article.setId(id);
        article.setStatus(1); // 发布状态

        boolean updated = updateById(article);
        if (!updated) {
            throw new RuntimeException("发布失败：文章不存在或更新失败");
        }
    }

    @Override
    @ArticleSync(action = "view", description = "浏览了1篇文章")
    public void addViewArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        if (dbArticle == null) {
            throw new RuntimeException("文章不存在");
        }
        if (dbArticle.getStatus() != 1) {
            throw new RuntimeException("文章未发布，无法增加阅读量");
        }
        // 获取当前的文章的修改日期
        LocalDateTime updateAt = dbArticle.getUpdateAt();
        // 增加阅读量
        Article article = new Article();
        article.setId(id);
        article.setViews(dbArticle.getViews() + 1); // 发布状态
        article.setUpdateAt(updateAt); // 保持原有的更新时间

        boolean updated = updateById(article);
        if (!updated) {
            throw new RuntimeException("更新失败：文章不存在或更新失败");
        }
    }

    @Override
    public List<Article> listUnpublishedArticles() {
        return articleMapper.selectList(
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));
    }

    @Override
    public IPage<Article> listUnpublishedArticles(Page<Article> page) {
        return articleMapper.selectPage(page,
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));
    }

    @Override
    public IPage<ArticleWithCategoryVO> listUnpublishedArticlesWithCategory(Page<Article> page) {
        IPage<Article> resultPage = articleMapper.selectPage(page,
                new LambdaQueryWrapper<Article>().eq(Article::getStatus, 0));

        // 转换为VO对象并补充分类信息
        List<ArticleWithCategoryVO> voList = resultPage.getRecords().stream().map(article -> {
            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);

            // 查询作者用户名
            User user = userService.getById(article.getUserId());
            vo.setUsername(user != null ? user.getName() : "");

            // 查询子分类和主分类信息
            if (article.getSubCategoryId() != null) {
                SubCategory subCategory = subCategoryMapper.selectById(article.getSubCategoryId());
                if (subCategory != null) {
                    vo.setSubCategoryName(subCategory.getName());
                    // 查询主分类信息
                    Category category = categoryMapper.selectById(subCategory.getCategoryId());
                    if (category != null) {
                        vo.setCategoryId(category.getId());
                        vo.setCategoryName(category.getName());
                    }
                }
            }

            return vo;
        }).toList();

        // 创建新的IPage对象，包含转换后的VO列表
        Page<ArticleWithCategoryVO> voPage = new Page<>(page.getCurrent(), page.getSize(), resultPage.getTotal());
        voPage.setRecords(voList);
        return voPage;
    }

    @Override
    public Article findByArticleTitle(String articleTitle) {
        return articleMapper.selectOne(
                new LambdaQueryWrapper<Article>().eq(Article::getTitle, articleTitle));
    }

    @Override
    public List<Article> listAllArticlesByTitle(String articleTitle) {
        return articleMapper.selectList(
                new LambdaQueryWrapper<Article>().like(Article::getTitle, articleTitle));
    }

}
