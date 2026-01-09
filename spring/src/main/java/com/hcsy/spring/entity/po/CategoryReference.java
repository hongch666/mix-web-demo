package com.hcsy.spring.entity.po;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.FieldStrategy;

import lombok.Data;

@Data
@TableName("category_reference") // 对应数据库中的表名
public class CategoryReference {
    @TableId
    private Long id;
    private Long subCategoryId; // 子分类ID
    private String type; // 类型：link 或 pdf
    @TableField(updateStrategy = FieldStrategy.IGNORED)
    private String link; // 官网链接
    @TableField(updateStrategy = FieldStrategy.IGNORED)
    private String pdf; // PDF链接（OSS）
}
