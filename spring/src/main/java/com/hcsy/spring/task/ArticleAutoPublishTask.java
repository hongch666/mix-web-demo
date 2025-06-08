package com.hcsy.spring.task;

import com.hcsy.spring.po.Article;
import com.hcsy.spring.service.ArticleService;
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

    // 每天 0 点执行
    @Scheduled(cron = "0 0 0 * * ?")
    public void autoPublishUnpublishedArticles() {
        log.info("定时任务启动：检查未发布文章");

        List<Article> articles = articleService.listUnpublishedArticles();
        if (articles.isEmpty()) {
            log.info("无未发布文章");
            return;
        }

        for (Article article : articles) {
            try {
                articleService.publishArticle(article.getId());
                log.info("自动发布文章成功：id={}", article.getId());
            } catch (Exception e) {
                log.error("自动发布文章失败：id=" + article.getId(), e);
            }
        }

        log.info("定时任务结束：共处理 {} 篇未发布文章", articles.size());
    }
}
