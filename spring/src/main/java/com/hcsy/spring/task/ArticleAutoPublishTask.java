package com.hcsy.spring.task;

import com.hcsy.spring.po.Article;
import com.hcsy.spring.service.ArticleService;
import com.hcsy.spring.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class ArticleAutoPublishTask {

    private final ArticleService articleService;
    private final SimpleLogger logger;

    // 每小时执行一次
    @Scheduled(cron = "*/5 * * * * ?")
    public void autoPublishUnpublishedArticles() {
        logger.info("定时任务启动：检查未发布文章");

        List<Article> articles = articleService.listUnpublishedArticles();
        if (articles.isEmpty()) {
            logger.info("无未发布文章");
            return;
        }

        for (Article article : articles) {
            try {
                articleService.publishArticle(article.getId());
                logger.info("自动发布文章成功：id=%d", article.getId());
            } catch (Exception e) {
                logger.error("自动发布文章失败：id=" + article.getId(), e);
            }
        }

        logger.info("定时任务结束：共处理 %d 篇未发布文章", articles.size());
    }
}
