package com.hcsy.spring.api.service;

import java.util.Collection;

import com.hcsy.spring.entity.po.SubCategory;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface SubCategoryService {
    Mono<SubCategory> getById(Long id);

    Flux<SubCategory> listByIds(Collection<Long> ids);
}
