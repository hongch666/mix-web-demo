package com.hcsy.spring.api.service;

import java.util.List;
import java.util.Map;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.vo.ArticleSearchDocVO;
import com.hcsy.spring.entity.vo.ArticleStatisticsAnalyzeVO;
import com.hcsy.spring.entity.vo.ArticleStatisticVO;
import com.hcsy.spring.entity.vo.ArticleWithCategoryVO;
import com.hcsy.spring.entity.vo.AiCommentContextVO;
import com.hcsy.spring.entity.vo.CategoryArticleCountVO;
import com.hcsy.spring.entity.vo.CursorPageVO;
import com.hcsy.spring.entity.vo.MonthlyCountVO;

public interface ArticleService extends IService<Article> {
    List<Article> listPublishedArticles();

    IPage<Article> listPublishedArticles(Page<Article> page);

    boolean saveArticle(Article article);

    boolean updateArticle(Article article);

    boolean deleteArticle(Long id);

    boolean deleteArticles(List<Long> ids);

    IPage<Article> listArticlesById(Page<Article> page, Integer id);

    IPage<Article> listArticlesById(Page<Article> page, Integer id, boolean onlyPublished);

    void publishArticle(Long id);

    void addViewArticle(Long id);

    List<Article> listUnpublishedArticles();

    IPage<Article> listUnpublishedArticles(Page<Article> page);

    IPage<com.hcsy.spring.entity.vo.ArticleWithCategoryVO> listUnpublishedArticlesWithCategory(Page<Article> page);

    IPage<com.hcsy.spring.entity.vo.ArticleWithCategoryVO> listArticlesByIdWithCategory(Page<Article> page, Integer id, boolean onlyPublished);

    Article findByArticleTitle(String articleTitle);

    List<Article> listAllArticlesByTitle(String articleTitle);

    List<ArticleWithCategoryVO> listByIds(List<Long> ids);

    CursorPageVO<ArticleSearchDocVO> listSearchDocs(Long cursor, Integer size);

    Map<Long, ArticleStatisticVO> getSearchStats(List<Long> ids);

    List<ArticleSearchDocVO> listTopArticles(Integer limit);

    ArticleStatisticsAnalyzeVO getAnalyzeStatistics();

    List<CategoryArticleCountVO> countArticlesByCategory();

    List<MonthlyCountVO> countMonthlyPublishedArticles(Integer months);

    CursorPageVO<ArticleSearchDocVO> listExportRows(Long cursor, Integer size);

    AiCommentContextVO getAiCommentContext(Long id);

}
