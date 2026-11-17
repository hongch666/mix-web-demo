package com.hcsy.spring.application.service.impl;

import static org.mockito.Mockito.when;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hcsy.spring.entity.po.CategoryReference;
import com.hcsy.spring.infra.repository.CategoryReferenceRepository;
import com.hcsy.spring.infra.repository.UserRepository;

import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class OssReferenceServiceImplTest {

    private static final String AVATAR = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/a.png";

    @Mock
    private UserRepository userRepository;
    @Mock
    private CategoryReferenceRepository categoryReferenceRepository;

    private OssReferenceServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new OssReferenceServiceImpl(userRepository, categoryReferenceRepository);
    }

    // 通过 Repository 查询两表原始链接，合并去重后返回，空值被过滤
    @Test
    @DisplayName("两表原始链接合并去重并过滤空值")
    void mergesAndDeduplicatesReferences() {
        when(userRepository.findAllImgs()).thenReturn(Flux.just(AVATAR, ""));
        when(categoryReferenceRepository.findAllWithPdfOrLink()).thenReturn(
            Flux.just(
                reference("https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pdf/guide.pdf",
                    "https://example.com/doc"),
                reference("", AVATAR)));

        StepVerifier.create(service.listOssReferenceUrls())
            .assertNext(urls -> {
                // Spring 只返回原始链接并按空值过滤、去重；域名过滤由 NestJS 侧完成
                org.junit.jupiter.api.Assertions.assertEquals(3, urls.size());
                org.junit.jupiter.api.Assertions.assertTrue(urls.contains(AVATAR));
                org.junit.jupiter.api.Assertions.assertTrue(
                    urls.contains("https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pdf/guide.pdf"));
                org.junit.jupiter.api.Assertions.assertTrue(
                    urls.contains("https://example.com/doc"));
            })
            .verifyComplete();
    }

    // pdf 或 link 为 NULL 时只返回有值的链接，不能因 null 元素报错
    @Test
    @DisplayName("单列 NULL 的参考记录不报错且只返回有效链接")
    void skipsNullColumnReferences() {
        when(userRepository.findAllImgs()).thenReturn(Flux.empty());
        when(categoryReferenceRepository.findAllWithPdfOrLink()).thenReturn(
            Flux.just(
                reference(null, "https://example.com/doc"),
                reference("https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pdf/a.pdf", null),
                reference(null, null)));

        StepVerifier.create(service.listOssReferenceUrls())
            .assertNext(urls -> {
                org.junit.jupiter.api.Assertions.assertEquals(2, urls.size());
                org.junit.jupiter.api.Assertions.assertTrue(urls.contains("https://example.com/doc"));
                org.junit.jupiter.api.Assertions.assertTrue(
                    urls.contains("https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pdf/a.pdf"));
            })
            .verifyComplete();
    }

    // 两表均无数据时返回空列表
    @Test
    @DisplayName("无在用引用时返回空列表")
    void returnsEmptyWhenNoReferences() {
        when(userRepository.findAllImgs()).thenReturn(Flux.empty());
        when(categoryReferenceRepository.findAllWithPdfOrLink()).thenReturn(Flux.empty());

        StepVerifier.create(service.listOssReferenceUrls())
            .assertNext(urls -> org.junit.jupiter.api.Assertions.assertTrue(urls.isEmpty()))
            .verifyComplete();
    }

    private CategoryReference reference(String pdf, String link) {
        CategoryReference reference = new CategoryReference();
        reference.setPdf(pdf);
        reference.setLink(link);
        return reference;
    }
}
