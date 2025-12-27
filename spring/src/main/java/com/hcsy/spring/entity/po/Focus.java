package com.hcsy.spring.entity.po;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("focus")
public class Focus {
    @TableId
    private Long id;
    private Long userId;
    private Long focusId;
    private LocalDateTime createdTime;
}
