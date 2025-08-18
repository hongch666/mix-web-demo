package com.hcsy.spring.common.config;

import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.jsontype.BasicPolymorphicTypeValidator;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.cache.CacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Configuration
public class RedisCacheConfig {

        @Bean
        public CacheManager cacheManager(RedisConnectionFactory factory) {
                // 自定义 ObjectMapper，注册 JavaTimeModule 以支持 LocalDateTime 等日期时间类型
                ObjectMapper objectMapper = new ObjectMapper();
                objectMapper.registerModule(new JavaTimeModule());
                objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
                // 启用多态类型处理，确保序列化时写入类型信息，反序列化能恢复为具体类型（如 Page）
                objectMapper.activateDefaultTyping(
                                BasicPolymorphicTypeValidator.builder().allowIfBaseType(Object.class).build(),
                                ObjectMapper.DefaultTyping.NON_FINAL, JsonTypeInfo.As.PROPERTY);

                GenericJackson2JsonRedisSerializer valueSerializer = new GenericJackson2JsonRedisSerializer(
                                objectMapper);
                StringRedisSerializer keySerializer = new StringRedisSerializer();

                RedisSerializationContext.SerializationPair<Object> pair = RedisSerializationContext.SerializationPair
                                .fromSerializer(valueSerializer);

                RedisCacheConfiguration defaultConfig = RedisCacheConfiguration.defaultCacheConfig()
                                .serializeKeysWith(RedisSerializationContext.SerializationPair
                                                .fromSerializer(keySerializer))
                                .serializeValuesWith(pair)
                                .entryTtl(Duration.ofMinutes(30));

                Map<String, RedisCacheConfiguration> configs = new HashMap<>();
                configs.put("categoryById", defaultConfig.entryTtl(Duration.ofMinutes(60)));
                configs.put("categoryPage", defaultConfig.entryTtl(Duration.ofMinutes(5)));

                return RedisCacheManager.builder(factory)
                                .cacheDefaults(defaultConfig)
                                .withInitialCacheConfigurations(configs)
                                .build();
        }
}
