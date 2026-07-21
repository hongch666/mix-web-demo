package com.hcsy.spring.core.config;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.ReactiveRedisConnectionFactory;
import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.jsontype.BasicPolymorphicTypeValidator;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

@Configuration
public class ReactiveRedisConfig {

    @SuppressWarnings("null")
    @Bean
    ReactiveRedisTemplate<String, Object> reactiveRedisTemplate(
            @Qualifier("redisConnectionFactory") ReactiveRedisConnectionFactory factory) {
        // 自定义 ObjectMapper，注册 JavaTimeModule 以支持 LocalDateTime 等日期时间类型
        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());
        objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        // 启用多态类型处理，确保序列化时写入类型信息
        objectMapper.activateDefaultTyping(
            BasicPolymorphicTypeValidator.builder().allowIfBaseType(Object.class).build(),
            ObjectMapper.DefaultTyping.NON_FINAL,
            JsonTypeInfo.As.PROPERTY);

        GenericJackson2JsonRedisSerializer valueSerializer = new GenericJackson2JsonRedisSerializer(objectMapper);
        StringRedisSerializer keySerializer = new StringRedisSerializer();

        RedisSerializationContext.SerializationPair<Object> pair = RedisSerializationContext
            .SerializationPair
            .fromSerializer(valueSerializer);

        RedisSerializationContext<String, Object> context = RedisSerializationContext
            .<String, Object>newSerializationContext(keySerializer)
            .value(pair)
            .build();

        return new ReactiveRedisTemplate<>(factory, context);
    }
}
