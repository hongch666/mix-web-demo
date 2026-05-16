package com.hcsy.spring.entity.vo;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CursorPageVO<T> {
    private Long nextCursor;
    private Boolean hasMore;
    private List<T> list;
}
