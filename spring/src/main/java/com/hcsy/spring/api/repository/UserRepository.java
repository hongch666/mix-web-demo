package com.hcsy.spring.api.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Modifying;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.User;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface UserRepository extends ReactiveCrudRepository<User, Long> {
    Mono<User> findByName(String name);

    Mono<User> findByEmail(String email);

    Mono<User> findByGithubId(Long githubId);

    Flux<User> findByNameContaining(String name);

    Flux<User> findByRoleNotOrderByIdAsc(String role);

    Flux<User> findByRoleNotAndNameContainingOrderByIdAsc(String role, String name);

    Flux<User> findByRoleNotOrderByIdAsc(String role, Pageable pageable);

    Flux<User> findByRoleNotAndNameContainingOrderByIdAsc(String role, String name, Pageable pageable);

    Flux<User> findByRoleOrderByIdAsc(String role);

    Mono<Long> countByRoleNot(String role);

    Mono<Long> countByRoleNotAndNameContaining(String role, String name);

    Mono<Long> countByRole(String role);

    @Query("SELECT id FROM user WHERE role <> :role ORDER BY id")
    Flux<Long> findIdsByRoleNot(@Param("role") String role);

    @Query("SELECT id FROM user WHERE role = :role ORDER BY id")
    Flux<Long> findIdsByRole(@Param("role") String role);

    @Modifying
    @Query("UPDATE user SET password = :password")
    Mono<Integer> updateAllPasswords(@Param("password") String password);

    /**
     * 查询 update_at > :after 的用户，用于Neo4j增量同步（user表列名为update_at）
     */
    @Query("SELECT * FROM user WHERE update_at > :after")
    Flux<User> findByUpdateAtAfter(@Param("after") LocalDateTime after);
}
