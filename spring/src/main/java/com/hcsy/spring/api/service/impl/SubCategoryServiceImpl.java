package com.hcsy.spring.api.service.impl;

import java.util.Collection;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.api.service.SubCategoryService;
import com.hcsy.spring.entity.po.SubCategory;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class SubCategoryServiceImpl implements SubCategoryService {

    private final SubCategoryRepository subCategoryRepository;

    @SuppressWarnings("null")
    @Override
    public Mono<SubCategory> getById(Long id) {
        return subCategoryRepository.findById(id);
    }

    @SuppressWarnings("null")
    @Override
    public Flux<SubCategory> listByIds(Collection<Long> ids) {
        return subCategoryRepository.findAllById(ids);
    }
}
