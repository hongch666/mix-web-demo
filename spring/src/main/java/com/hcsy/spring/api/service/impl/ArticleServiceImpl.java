package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.ArticleMapper;
import com.hcsy.spring.api.mapper.CategoryMapper;
import com.hcsy.spring.api.mapper.ArticleCollectMapper;
import com.hcsy.spring.api.mapper.ArticleLikeMapper;
import com.hcsy.spring.api.mapper.CommentsMapper;
import com.hcsy.spring.api.mapper.FocusMapper;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.ArticleService;
import com.hcsy.spring.api.service.CategoryReferenceService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.HttpCode;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.ArticleSearchDocVO;
import com.hcsy.spring.entity.vo.ArticleStatisticsAnalyzeVO;
import com.hcsy.spring.entity.vo.ArticleStatisticVO;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import com.hcsy.spring.entity.vo.AiCommentContextVO;
import com.hcsy.spring.entity.vo.CategoryArticleCountVO;
import com.hcsy.spring.entity.vo.CursorPageVO;
import com.hcsy.spring.entity.vo.MonthlyCountVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl extends ServiceImpl<ArticleMapper, Article> implements ArticleService {
    private final ArticleMapper articleMapper;
    private final UserService userService;
    private final CategoryMapper categoryMapper;
    private final SubCategoryMapper subCategoryMapper;
    private final ArticleLikeMapper articleLikeMapper;
    private final ArticleCollectMapper articleCollectMapper;
    private final CommentsMapper commentsMapper;
    private final FocusMapper focusMapper;
    private final CategoryReferenceService categoryReferenceService;

    @Override
    public List<Article> listPublishedArticles() {
        return lambdaQuery()
                .eq(Article::getStatus, 1)
                .list();
    }

    @Override
    public IPage<ArticleWithCategoryVO> listArticlesByIdWithCategory(Page<Article> page, Integer id, boolean onlyPublished) {
        IPage<Article> resultPage = listArticlesById(page, id, onlyPublished);

        // 转换为VO对象并补充分类和用户信息
        List<ArticleWithCategoryVO> voList = resultPage.getRecords().stream().map(article -> {
            if (article.getSubCategoryId() == null) {
                throw new BusinessException(HttpCode.NOT_FOUND, Constants.UNDEFINED_SUB_CATEGORY_ID);
            }

            ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);

            // 查询作者用户名
            User user = userService.getById(article.getUserId());
            vo.setUsername(user != null ? user.getName() : Constants.DEFAULT_USER);

            // 查询子分类信息
            SubCategory subCategory = subCategoryMapper.selectById(article.getSubCategoryId());
            vo.setSubCategoryName(subCategory.getName());

            // 查询主分类信息
            Category category = categoryMapper.selectById(subCategory.getCategoryId());
            vo.setCategoryName(category.getName());

            return vo;
        }).toList();

        // 创建新的IPage对象，包含转换后的VO列表
        Page<ArticleWithCategoryVO> voPage = new Page<>(page.getCurrent(), page.getSize(), resultPage.getTotal());
        voPage.setRecords(voList);
        return voPage;
    }

    @Override
    public IPage<Article> listPublishedArticles(Page<Article> page) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getStatus, 1); // 只查已发布
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    public IPage<Article> listArticlesById(Page<Article> page, Integer id) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getUserId, id);
        queryWrapper.orderByAsc(Article::getCreateAt); // 按创建时间倒序

        return this.page(page, queryWrapper);
    }

    @Override
    public IPage<Article> listArticlesById(Page<Article> page, Integer id, boolean onlyPublished) {
        LambdaQueryWrapper<Article> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Article::getUserId, id);
        if (onlyPublished) {
            queryWrapper.eq(Article::getStatus, 1); // 只查已发布
        }
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
        articleMapper.updateById(article);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "delete", description = "删除了1篇文章")
    public boolean deleteArticle(Long id) {
        Article existing = articleMapper.selectById(id);
        if (existing == null) {
            throw new BusinessException(HttpCode.NOT_FOUND, Constants.UNDEFINED_ARTICLE_ID + id);
        }
        articleMapper.deleteById(id);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "delete", description = "批量删除文章")
    public boolean deleteArticles(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return true;
        }

        // 批量删除前校验：必须全部存在（只要有一个不存在就抛异常）
        List<Long> distinctIds = ids.stream()
                .filter(id -> id != null)
                .distinct()
                .toList();
        if (distinctIds.isEmpty()) {
            return true;
        }

        List<Article> existingList = articleMapper.selectBatchIds(distinctIds);
        if (existingList.size() != distinctIds.size()) {
            throw new BusinessException(HttpCode.NOT_FOUND, Constants.UNDEFINED_ARTICLES);
        }

        articleMapper.deleteBatchIds(ids);
        return true;
    }

    @Override
    @Transactional
    @ArticleSync(action = "publish", description = "发布了1篇文章")
    public void publishArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        if (dbArticle == null) {
            throw new BusinessException(HttpCode.NOT_FOUND, Constants.UNDEFINED_ARTICLE);
        }

        // 执行发布
        Article article = new Article();
        article.setId(id);
        article.setStatus(1); // 发布状态

        boolean updated = updateById(article);
        if (!updated) {
            throw new BusinessException(HttpCode.UNPROCESSABLE_ENTITY, Constants.PUBLISH_ARTICLE);
        }
    }

    @Override
    @Transactional
    @ArticleSync(action = "view", description = "浏览了1篇文章")
    public void addViewArticle(Long id) {
        // 查询文章所属用户ID
        Article dbArticle = articleMapper.selectById(id);
        if (dbArticle == null) {
            throw new BusinessException(HttpCode.NOT_FOUND, Constants.UNDEFINED_ARTICLE);
        }
        if (dbArticle.getStatus() != 1) {
            throw new BusinessException(HttpCode.UNPROCESSABLE_ENTITY, Constants.UNPUBLISH_ADD_VIEW);
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
            throw new BusinessException(HttpCode.UNPROCESSABLE_ENTITY, Constants.ADD_VIEW_ARTICLE);
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
            vo.setUsername(user != null ? user.getName() : Constants.DEFAULT_USER);

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

    @Override
    public List<ArticleWithCategoryVO> listByIds(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return Collections.emptyList();
        }
        return articleMapper.selectBatchIds(ids).stream()
                .map(this::toArticleWithCategoryVO)
                .toList();
    }

    @Override
    public CursorPageVO<ArticleSearchDocVO> listSearchDocs(Long cursor, Integer size) {
        int pageSize = Math.min(Math.max(size == null ? 500 : size, 1), 1000);
        List<Article> articles = articleMapper.selectList(
                Wrappers.<Article>lambdaQuery()
                        .eq(Article::getStatus, 1)
                        .gt(cursor != null && cursor > 0, Article::getId, cursor)
                        .orderByAsc(Article::getId)
                        .last("LIMIT " + (pageSize + 1)));

        boolean hasMore = articles.size() > pageSize;
        List<Article> currentPage = hasMore ? articles.subList(0, pageSize) : articles;
        List<Long> articleIds = currentPage.stream().map(Article::getId).toList();
        Map<Long, ArticleStatisticVO> statMap = getSearchStats(articleIds);
        List<ArticleSearchDocVO> docs = currentPage.stream()
                .map(article -> toSearchDoc(article, statMap.get(article.getId())))
                .toList();
        Long nextCursor = docs.isEmpty() ? (cursor == null ? 0L : cursor) : docs.get(docs.size() - 1).getId();
        return new CursorPageVO<>(nextCursor, hasMore, docs);
    }

    @Override
    public Map<Long, ArticleStatisticVO> getSearchStats(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return Collections.emptyMap();
        }
        List<Article> articles = articleMapper.selectBatchIds(ids);
        Map<Long, Long> userIdMap = articles.stream().collect(Collectors.toMap(Article::getId, Article::getUserId));
        Map<Long, Integer> viewsMap = articles.stream().collect(Collectors.toMap(Article::getId, article -> article.getViews() == null ? 0 : article.getViews()));
        Map<Long, Long> likeCountMap = articleLikeMapper.selectList(Wrappers.<ArticleLike>lambdaQuery().in(ArticleLike::getArticleId, ids))
                .stream().collect(Collectors.groupingBy(ArticleLike::getArticleId, Collectors.counting()));
        Map<Long, Long> collectCountMap = articleCollectMapper.selectList(Wrappers.<ArticleCollect>lambdaQuery().in(ArticleCollect::getArticleId, ids))
                .stream().collect(Collectors.groupingBy(ArticleCollect::getArticleId, Collectors.counting()));
        List<Long> userIds = userIdMap.values().stream().distinct().toList();
        Map<Long, Long> followCountMap = userIds.isEmpty() ? Collections.emptyMap()
                : focusMapper.selectList(Wrappers.<Focus>lambdaQuery().in(Focus::getFocusId, userIds))
                        .stream().collect(Collectors.groupingBy(Focus::getFocusId, Collectors.counting()));

        return ids.stream().collect(Collectors.toMap(Function.identity(), id -> {
            ArticleStatisticVO stat = new ArticleStatisticVO();
            stat.setArticleId(id);
            stat.setViews(viewsMap.getOrDefault(id, 0));
            stat.setLikeCount(likeCountMap.getOrDefault(id, 0L).intValue());
            stat.setCollectCount(collectCountMap.getOrDefault(id, 0L).intValue());
            stat.setAuthorFollowCount(followCountMap.getOrDefault(userIdMap.get(id), 0L).intValue());
            return stat;
        }));
    }

    @Override
    public List<ArticleSearchDocVO> listTopArticles(Integer limit) {
        int safeLimit = Math.min(Math.max(limit == null ? 10 : limit, 1), 100);
        List<Article> articles = articleMapper.selectList(
                Wrappers.<Article>lambdaQuery()
                        .eq(Article::getStatus, 1)
                        .orderByDesc(Article::getViews)
                        .last("LIMIT " + safeLimit));
        Map<Long, ArticleStatisticVO> statMap = getSearchStats(articles.stream().map(Article::getId).toList());
        return articles.stream().map(article -> toSearchDoc(article, statMap.get(article.getId()))).toList();
    }

    @Override
    public ArticleStatisticsAnalyzeVO getAnalyzeStatistics() {
        List<Article> publishedArticles = articleMapper.selectList(
                Wrappers.<Article>lambdaQuery().eq(Article::getStatus, 1));
        List<Long> articleIds = publishedArticles.stream().map(Article::getId).toList();
        ArticleStatisticsAnalyzeVO vo = new ArticleStatisticsAnalyzeVO();
        long totalArticles = publishedArticles.size();
        long totalViews = publishedArticles.stream().mapToLong(article -> article.getViews() == null ? 0 : article.getViews()).sum();
        long activeAuthors = publishedArticles.stream().map(Article::getUserId).distinct().count();
        long totalLikes = articleIds.isEmpty() ? 0L : articleLikeMapper.selectCount(Wrappers.<ArticleLike>lambdaQuery().in(ArticleLike::getArticleId, articleIds));
        long totalCollects = articleIds.isEmpty() ? 0L : articleCollectMapper.selectCount(Wrappers.<ArticleCollect>lambdaQuery().in(ArticleCollect::getArticleId, articleIds));
        vo.setTotalArticles(totalArticles);
        vo.setTotalViews(totalViews);
        vo.setActiveAuthors(activeAuthors);
        vo.setAverageViews(totalArticles == 0 ? 0.0D : (double) totalViews / totalArticles);
        vo.setTotalLikes(totalLikes);
        vo.setAverageLikes(totalArticles == 0 ? 0.0D : (double) totalLikes / totalArticles);
        vo.setTotalCollects(totalCollects);
        vo.setAverageCollects(totalArticles == 0 ? 0.0D : (double) totalCollects / totalArticles);
        return vo;
    }

    @Override
    public List<CategoryArticleCountVO> countArticlesByCategory() {
        List<Category> categories = categoryMapper.selectList(Wrappers.lambdaQuery(Category.class));
        List<SubCategory> subCategories = subCategoryMapper.selectList(Wrappers.lambdaQuery(SubCategory.class));
        Map<Long, Long> subToCategory = subCategories.stream()
                .collect(Collectors.toMap(SubCategory::getId, SubCategory::getCategoryId));
        Map<Long, Long> countMap = articleMapper.selectList(Wrappers.<Article>lambdaQuery().eq(Article::getStatus, 1))
                .stream()
                .filter(article -> article.getSubCategoryId() != null)
                .collect(Collectors.groupingBy(article -> subToCategory.get(article.getSubCategoryId().longValue()), Collectors.counting()));
        return categories.stream()
                .map(category -> new CategoryArticleCountVO(category.getId(), category.getName(), countMap.getOrDefault(category.getId(), 0L)))
                .sorted((left, right) -> Long.compare(right.getArticleCount(), left.getArticleCount()))
                .toList();
    }

    @Override
    public List<MonthlyCountVO> countMonthlyPublishedArticles(Integer months) {
        int safeMonths = Math.min(Math.max(months == null ? 6 : months, 1), 24);
        YearMonth now = YearMonth.now();
        Map<String, Long> countMap = articleMapper.selectList(Wrappers.<Article>lambdaQuery().eq(Article::getStatus, 1))
                .stream()
                .filter(article -> article.getCreateAt() != null)
                .collect(Collectors.groupingBy(article -> YearMonth.from(article.getCreateAt()).format(DateTimeFormatter.ofPattern("yyyy-MM")), Collectors.counting()));
        Map<String, Long> ordered = new LinkedHashMap<>();
        for (int i = safeMonths - 1; i >= 0; i--) {
            String month = now.minusMonths(i).format(DateTimeFormatter.ofPattern("yyyy-MM"));
            ordered.put(month, countMap.getOrDefault(month, 0L));
        }
        return ordered.entrySet().stream().map(entry -> new MonthlyCountVO(entry.getKey(), entry.getValue())).toList();
    }

    @Override
    public CursorPageVO<ArticleSearchDocVO> listExportRows(Long cursor, Integer size) {
        return listSearchDocs(cursor, size);
    }

    @Override
    public AiCommentContextVO getAiCommentContext(Long id) {
        Article article = articleMapper.selectById(id);
        if (article == null) {
            throw new BusinessException(HttpCode.NOT_FOUND, Constants.UNDEFINED_ARTICLE);
        }
        AiCommentContextVO vo = BeanUtil.copyProperties(article, AiCommentContextVO.class);
        if (article.getSubCategoryId() != null) {
            vo.setSubCategoryId(article.getSubCategoryId().longValue());
            vo.setCategoryReference(categoryReferenceService.getCategoryReferenceBySubCategoryId(article.getSubCategoryId().longValue()));
        }
        return vo;
    }

    private ArticleWithCategoryVO toArticleWithCategoryVO(Article article) {
        ArticleWithCategoryVO vo = BeanUtil.copyProperties(article, ArticleWithCategoryVO.class);
        User user = userService.getById(article.getUserId());
        vo.setUsername(user != null ? user.getName() : Constants.DEFAULT_USER);
        fillCategory(vo, article.getSubCategoryId());
        return vo;
    }

    private ArticleSearchDocVO toSearchDoc(Article article, ArticleStatisticVO stat) {
        ArticleWithCategoryVO categoryVO = toArticleWithCategoryVO(article);
        ArticleSearchDocVO doc = BeanUtil.copyProperties(categoryVO, ArticleSearchDocVO.class);
        ArticleStatisticVO safeStat = stat == null ? new ArticleStatisticVO() : stat;
        doc.setViews(safeStat.getViews() == null ? 0 : safeStat.getViews());
        doc.setLikeCount(safeStat.getLikeCount() == null ? 0 : safeStat.getLikeCount());
        doc.setCollectCount(safeStat.getCollectCount() == null ? 0 : safeStat.getCollectCount());
        doc.setAuthorFollowCount(safeStat.getAuthorFollowCount() == null ? 0 : safeStat.getAuthorFollowCount());

        List<Comments> comments = commentsMapper.selectList(Wrappers.<Comments>lambdaQuery().eq(Comments::getArticleId, article.getId()));
        List<Long> userIds = comments.stream().map(Comments::getUserId).distinct().toList();
        Map<Long, String> roleMap = userIds.isEmpty() ? Collections.emptyMap()
                : userService.listByIds(userIds).stream().collect(Collectors.toMap(User::getId, User::getRole));
        List<Comments> aiComments = comments.stream().filter(comment -> "ai".equalsIgnoreCase(roleMap.get(comment.getUserId()))).toList();
        List<Comments> userComments = comments.stream().filter(comment -> !"ai".equalsIgnoreCase(roleMap.get(comment.getUserId()))).toList();
        doc.setAiCommentCount(aiComments.size());
        doc.setUserCommentCount(userComments.size());
        doc.setAiScore(averageStar(aiComments));
        doc.setUserScore(averageStar(userComments));
        return doc;
    }

    private Double averageStar(List<Comments> comments) {
        return comments.stream()
                .filter(comment -> comment.getStar() != null)
                .mapToDouble(Comments::getStar)
                .average()
                .orElse(0.0D);
    }

    private void fillCategory(ArticleWithCategoryVO vo, Integer subCategoryId) {
        if (subCategoryId == null) {
            return;
        }
        SubCategory subCategory = subCategoryMapper.selectById(subCategoryId);
        if (subCategory == null) {
            return;
        }
        vo.setSubCategoryName(subCategory.getName());
        Category category = categoryMapper.selectById(subCategory.getCategoryId());
        if (category != null) {
            vo.setCategoryId(category.getId());
            vo.setCategoryName(category.getName());
        }
    }

}
