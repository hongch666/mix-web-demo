package com.hcsy.spring.common.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import com.hcsy.spring.entity.po.Result;

@FeignClient(name = "spring-category")
public interface CategoryClient {

    @GetMapping("/category/single/{id}")
    Result getSingleCategoryById(@PathVariable Long id);

    @GetMapping("/category/sub/single/{id}")
    Result getSingleSubCategoryById(@PathVariable Integer id);
}
