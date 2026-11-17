package com.hcsy.spring.application.service.impl;

import java.util.Arrays;
import java.util.List;

import org.springframework.stereotype.Service;

import com.hcsy.spring.application.service.OssReferenceService;
import com.hcsy.spring.infra.repository.CategoryReferenceRepository;
import com.hcsy.spring.infra.repository.UserRepository;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * OSS 在用引用查询服务，通过 Repository 扫描 Spring 库中的用户头像与分类权威参考文本，
 * 返回原始链接由调用方（NestJS）按自身 OSS 配置解析对象 key
 */
@Service
@RequiredArgsConstructor
public class OssReferenceServiceImpl implements OssReferenceService {
    private final UserRepository userRepository;
    private final CategoryReferenceRepository categoryReferenceRepository;

    /**
     * 查询 Spring 库中在用的 OSS 原始链接，两表合并去重后返回
     */
    @Override
    public Mono<List<String>> listOssReferenceUrls() {
        Flux<String> fromUser = userRepository.findAllImgs()
            .filter(url -> url != null && !url.isBlank());

        Flux<String> fromReference = categoryReferenceRepository.findAllWithPdfOrLink()
            .flatMap(reference -> Flux.fromIterable(Arrays.asList(
                reference.getPdf(),
                reference.getLink())))
            .filter(url -> url != null && !url.isBlank());

        return Flux.concat(fromUser, fromReference).distinct().collectList();
    }
}
