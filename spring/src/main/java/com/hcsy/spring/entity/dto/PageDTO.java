package com.hcsy.spring.entity.dto;

import java.io.Serializable;
import java.util.List;

import lombok.Data;

@Data
public class PageDTO<T> implements Serializable {
    private long current;
    private long size;
    private long total;
    private List<T> records;
}
