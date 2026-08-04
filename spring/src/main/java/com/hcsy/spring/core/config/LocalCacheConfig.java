package com.hcsy.spring.core.config;

import java.time.Duration;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.ReactiveRedisConnectionFactory;
import org.springframework.data.redis.listener.ReactiveRedisMessageListenerContainer;

import com.github.benmanes.caffeine.cache.AsyncCache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.github.benmanes.caffeine.cache.Expiry;
import com.hcsy.spring.common.cache.CategoryLocalCache;
import com.hcsy.spring.common.cache.UserLocalCache;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.vo.CategoryVO;
import com.hcsy.spring.entity.vo.UserListVO;

@Configuration
public class LocalCacheConfig {
    private static final Duration CATEGORY_CACHE_TTL = Duration.ofHours(24);
    private static final Duration ALL_USERS_CACHE_TTL = Duration.ofHours(24);
    private static final Duration EMPTY_USERS_CACHE_TTL = Duration.ofMinutes(10);

    @SuppressWarnings("unused")
    @Bean
    CategoryLocalCache categoryLocalCache() {
        AsyncCache<Long, CategoryVO> categoryByIdCache = Caffeine.<Long, CategoryVO>newBuilder()
            .maximumSize(1_000)
            .expireAfterWrite(CATEGORY_CACHE_TTL)
            .recordStats()
            .buildAsync();
        AsyncCache<String, PageDTO<CategoryVO>> categoryPageCache = Caffeine.<String, PageDTO<CategoryVO>>newBuilder()
            .maximumSize(200)
            .expireAfterWrite(CATEGORY_CACHE_TTL)
            .recordStats()
            .buildAsync();
        return new CategoryLocalCache(categoryByIdCache, categoryPageCache);
    }

    @SuppressWarnings("unused")
    @Bean
    UserLocalCache userLocalCache() {
        AsyncCache<String, UserListVO> allUsersCache = Caffeine.<String, UserListVO>newBuilder()
            .maximumSize(1)
            .expireAfter(new UserListCacheExpiry())
            .recordStats()
            .buildAsync();
        return new UserLocalCache(allUsersCache);
    }

    @SuppressWarnings("null")
    @Bean
    ReactiveRedisMessageListenerContainer reactiveRedisMessageListenerContainer(
        ReactiveRedisConnectionFactory connectionFactory) {
        return new ReactiveRedisMessageListenerContainer(connectionFactory);
    }

    private static final class UserListCacheExpiry implements Expiry<String, UserListVO> {
        @Override
        public long expireAfterCreate(String key, UserListVO value, long currentTime) {
            return isEmpty(value) ? EMPTY_USERS_CACHE_TTL.toNanos() : ALL_USERS_CACHE_TTL.toNanos();
        }

        @Override
        public long expireAfterUpdate(String key, UserListVO value, long currentTime, long currentDuration) {
            return currentDuration;
        }

        @Override
        public long expireAfterRead(String key, UserListVO value, long currentTime, long currentDuration) {
            return currentDuration;
        }

        private boolean isEmpty(UserListVO value) {
            return value.getTotal() != null && value.getTotal() == 0;
        }
    }
}
