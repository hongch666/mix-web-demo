package com.hcsy.spring.api.repository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.Category;

import reactor.core.publisher.Flux;

public interface CategoryRepository extends ReactiveCrudRepository<Category, Long> {
    Flux<Category> findAllByOrderByIdAsc(Pageable pageable);
}
