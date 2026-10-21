package com.hcsy.spring.application.service;

import java.util.Collection;

import com.hcsy.spring.entity.po.SubCategory;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 子分类业务接口，定义按ID单个与批量查询子分类的响应式操作
 */
public interface SubCategoryService {
    /**
     * 根据ID查询单个子分类，返回Mono响应式结果
     */
    Mono<SubCategory> getById(Long id);

    /**
     * 根据ID集合批量查询子分类，返回Flux响应式流
     */
    Flux<SubCategory> listByIds(Collection<Long> ids);
}
