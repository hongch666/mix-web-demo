package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

@Data
@TableName("focus")
public class Focus {
    @TableId
    private Long id;
    private Long userId;
    private Long focusId;
    private LocalDateTime createdTime;
}
