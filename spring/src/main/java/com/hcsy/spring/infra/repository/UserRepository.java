package com.hcsy.spring.infra.repository;

import java.time.LocalDateTime;

import org.springframework.data.domain.Pageable;
import org.springframework.data.r2dbc.repository.Modifying;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.repository.reactive.ReactiveCrudRepository;

import com.hcsy.spring.entity.po.User;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 负责用户实体（User）的响应式数据访问，含多种登录方式查找、角色筛选与密码重置
 */
public interface UserRepository extends ReactiveCrudRepository<User, Long> {
    /**
     * 按用户名精确查找用户，用于登录与用户名唯一性校验
     */
    Mono<User> findByName(String name);

    /**
     * 按邮箱查找用户，用于邮箱登录与注册校验
     */
    Mono<User> findByEmail(String email);

    /**
     * 按 GitHub 账号 ID 查找用户，用于 GitHub 登录时匹配已有账号
     */
    Mono<User> findByGithubId(Long githubId);

    /**
     * 按用户名模糊查询用户列表
     */
    Flux<User> findByNameContaining(String name);

    /**
     * 按 ID 升序查询指定角色之外的全部用户列表
     */
    Flux<User> findByRoleNotOrderByIdAsc(String role);

    /**
     * 按 ID 升序查询指定角色之外且用户名模糊匹配的全部用户列表
     */
    Flux<User> findByRoleNotAndNameContainingOrderByIdAsc(String role, String name);

    /**
     * 按 ID 升序分页查询指定角色之外的用户列表，用于普通用户分页
     */
    Flux<User> findByRoleNotOrderByIdAsc(String role, Pageable pageable);

    /**
     * 按 ID 升序分页查询指定角色之外且用户名模糊匹配的用户列表
     */
    Flux<User> findByRoleNotAndNameContainingOrderByIdAsc(String role, String name, Pageable pageable);

    /**
     * 按 ID 升序查询指定角色的全部用户列表，如 AI 用户
     */
    Flux<User> findByRoleOrderByIdAsc(String role);

    /**
     * 统计指定角色之外的用户数量
     */
    Mono<Long> countByRoleNot(String role);

    /**
     * 统计指定角色之外且用户名模糊匹配的用户数量
     */
    Mono<Long> countByRoleNotAndNameContaining(String role, String name);

    /**
     * 统计指定角色的用户数量
     */
    Mono<Long> countByRole(String role);

    /**
     * 查询指定角色之外的用户 ID 列表，用于批量同步普通用户
     */
    @Query("SELECT id FROM user WHERE role <> :role ORDER BY id")
    Flux<Long> findIdsByRoleNot(@Param("role") String role);

    /**
     * 查询指定角色的用户 ID 列表，用于批量同步 AI 用户
     */
    @Query("SELECT id FROM user WHERE role = :role ORDER BY id")
    Flux<Long> findIdsByRole(@Param("role") String role);

    /**
     * 将全部用户的密码重置为指定值，用于一键重置密码
     */
    @Modifying
    @Query("UPDATE user SET password = :password")
    Mono<Integer> updateAllPasswords(@Param("password") String password);

    /**
     * 查询 update_at > :after 的用户，用于Neo4j增量同步（user表列名为update_at）
     */
    @Query("SELECT * FROM user WHERE update_at > :after")
    Flux<User> findByUpdateAtAfter(@Param("after") LocalDateTime after);
}
