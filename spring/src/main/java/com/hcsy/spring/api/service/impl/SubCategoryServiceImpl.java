package com.hcsy.spring.api.service.impl;

import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.SubCategoryMapper;
import com.hcsy.spring.api.service.SubCategoryService;
import com.hcsy.spring.entity.po.SubCategory;

@Service
public class SubCategoryServiceImpl extends ServiceImpl<SubCategoryMapper, SubCategory> implements SubCategoryService {
}
