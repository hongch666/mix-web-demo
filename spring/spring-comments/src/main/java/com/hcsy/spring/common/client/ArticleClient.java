package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import com.hcsy.spring.entity.po.Result;

@FeignClient(name = "spring-article")
public interface ArticleClient {
    @GetMapping("/articles/comment-use/{id}")
    public Result getById(@PathVariable Long id);

    @GetMapping("/articles/comment-use/title/{title}")
    public Result findByArticleTitle(@PathVariable String title);

    @GetMapping("/articles/comment-use/all/{title}")
    public Result listAllArticlesByTitle(@PathVariable String title);
}
