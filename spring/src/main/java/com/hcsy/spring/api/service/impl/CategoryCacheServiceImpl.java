package com.hcsy.spring.api.service.impl;

import java.util.List;

import org.springframework.beans.BeanUtils;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.api.repository.CategoryRepository;
import com.hcsy.spring.api.repository.SubCategoryRepository;
import com.hcsy.spring.api.service.CategoryCacheService;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.RedisKeys;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.SubCategoryVO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class CategoryCacheServiceImpl implements CategoryCacheService {

    private static final String CATEGORY_PAGE_KEY = "category:page:p_%d_s_%d";
    private static final long CACHE_TTL_SECONDS = 24 * 60 * 60L;

    private final CategoryRepository categoryRepository;
    private final SubCategoryRepository subCategoryRepository;
    private final RedisUtil redisUtil;
    private final ObjectMapper objectMapper;
    private final SimpleLogger logger;

    @Override
    public Mono<CategoryVO> getCategoryById(Long id) {
        String cacheKey = RedisKeys.categoryId(id);
        return redisUtil.get(cacheKey)
                .flatMap(json -> readCache(json, CategoryVO.class, cacheKey))
                .onErrorResume(error -> cacheReadFallback(cacheKey, error))
                .switchIfEmpty(Mono.defer(() -> loadCategory(id)
                        .flatMap(category -> writeCache(cacheKey, category).thenReturn(category))));
    }

    @Override
    public Mono<PageDTO<CategoryVO>> cachedPageCategory(long page, long size) {
        String cacheKey = CATEGORY_PAGE_KEY.formatted(page, size);
        return redisUtil.get(cacheKey)
                .flatMap(json -> readCache(json, new TypeReference<PageDTO<CategoryVO>>() {
                }, cacheKey))
                .onErrorResume(error -> cacheReadFallback(cacheKey, error))
                .switchIfEmpty(Mono.defer(() -> loadCategoryPage(page, size)
                        .flatMap(result -> writeCache(cacheKey, result).thenReturn(result))));
    }

    @Override
    public Mono<Void> evictAllCategoryCaches() {
        return redisUtil.getKeys("category:*")
                .collectList()
                .flatMap(keys -> keys.isEmpty() ? Mono.empty() : redisUtil.delete(keys).then())
                .onErrorResume(error -> {
                    logger.error(Messages.CATEGORY_CACHE_EVICT_ALL_FAILED, error.getMessage(), error);
                    return Mono.empty();
                });
    }

    @Override
    public Mono<Void> evictCategoryByIdCache(Long id) {
        String cacheKey = RedisKeys.categoryId(id);
        return redisUtil.delete(cacheKey)
                .onErrorResume(error -> {
                    logger.error(Messages.CATEGORY_CACHE_EVICT_FAILED, cacheKey, error.getMessage(), error);
                    return Mono.just(false);
                })
                .then();
    }

    @SuppressWarnings("null")
    private Mono<CategoryVO> loadCategory(Long id) {
        logger.info(Messages.CATEGORY_CACHE);
        return categoryRepository.findById(id).flatMap(this::buildCategoryVO);
    }

    private Mono<PageDTO<CategoryVO>> loadCategoryPage(long page, long size) {
        logger.info(Messages.CATEGORY_CACHE_PAGE);
        PageRequest pageable = PageRequest.of(toPageIndex(page), toPageSize(size));
        Mono<List<CategoryVO>> records = categoryRepository.findAllByOrderByIdAsc(pageable)
                .flatMapSequential(this::buildCategoryVO)
                .collectList();
        Mono<Long> total = categoryRepository.count();

        return Mono.zip(records, total).map(result -> {
            PageDTO<CategoryVO> pageDTO = new PageDTO<>();
            pageDTO.setCurrent(page);
            pageDTO.setSize(size);
            pageDTO.setTotal(result.getT2());
            pageDTO.setRecords(result.getT1());
            return pageDTO;
        });
    }

    @SuppressWarnings("null")
    private Mono<CategoryVO> buildCategoryVO(Category category) {
        CategoryVO vo = new CategoryVO();
        BeanUtils.copyProperties(category, vo);
        return subCategoryRepository.findByCategoryIdOrderByIdAsc(category.getId())
                .map(subCategory -> {
                    SubCategoryVO subCategoryVO = new SubCategoryVO();
                    BeanUtils.copyProperties(subCategory, subCategoryVO);
                    return subCategoryVO;
                })
                .collectList()
                .map(subCategories -> {
                    vo.setSubCategories(subCategories);
                    return vo;
                });
    }

    private Mono<Void> writeCache(String key, Object value) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(value))
                .flatMap(json -> redisUtil.set(key, json, CACHE_TTL_SECONDS))
                .onErrorResume(error -> {
                    logger.error(Messages.CACHE_WRITE_FAILED, key, error.getMessage(), error);
                    return Mono.just(false);
                })
                .then();
    }

    private <T> Mono<T> readCache(String json, Class<T> type, String key) {
        return Mono.fromCallable(() -> objectMapper.readValue(json, type))
                .onErrorResume(error -> {
                    logger.error(Messages.CACHE_DESERIALIZE_FAILED, key, error.getMessage(), error);
                    return redisUtil.delete(key).then(Mono.empty());
                });
    }

    private <T> Mono<T> readCache(String json, TypeReference<T> type, String key) {
        return Mono.fromCallable(() -> objectMapper.readValue(json, type))
                .onErrorResume(error -> {
                    logger.error(Messages.CACHE_DESERIALIZE_FAILED, key, error.getMessage(), error);
                    return redisUtil.delete(key).then(Mono.empty());
                });
    }

    private <T> Mono<T> cacheReadFallback(String key, Throwable error) {
        logger.error(Messages.CACHE_READ_FAILED, key, error.getMessage(), error);
        return Mono.empty();
    }

    private int toPageIndex(long page) {
        return (int) Math.max(0, page - 1);
    }

    private int toPageSize(long size) {
        return (int) Math.max(1, Math.min(size, 1000));
    }
}
