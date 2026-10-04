package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 用户同步数据视图对象
 * 用于 Neo4j 同步接口，字段名与数据库列名保持一致
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "用户同步数据")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class UserSyncVO {

    @Schema(description = "用户ID")
    private Long id;

    @Schema(description = "用户名")
    private String name;

    @Schema(description = "邮箱")
    private String email;

    @Schema(description = "角色，如 user、admin、ai")
    private String role;

    @Schema(description = "头像地址")
    private String img;

    @Schema(description = "个性签名")
    private String signature;

    @Schema(description = "创建时间")
    private LocalDateTime createdAt;

    @Schema(description = "更新时间")
    private LocalDateTime updatedAt;
}
