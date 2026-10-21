package com.hcsy.spring.application.service.impl;

import java.util.Collection;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.SubCategoryService;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.infra.repository.SubCategoryRepository;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * SubCategoryService 的实现，直接委托仓储完成子分类的单个与批量查询
 */
@Service
@RequiredArgsConstructor
public class SubCategoryServiceImpl implements SubCategoryService {

    private final SubCategoryRepository subCategoryRepository;

    /**
     * 根据ID从仓储查询单个子分类并返回Mono响应式结果
     */
    @Override
    public Mono<SubCategory> getById(Long id) {
        return subCategoryRepository.findById(id);
    }

    /**
     * 根据ID集合从仓储批量查询子分类并返回Flux响应式流
     */
    @Override
    public Flux<SubCategory> listByIds(Collection<Long> ids) {
        return subCategoryRepository.findAllById(ids);
    }
}
