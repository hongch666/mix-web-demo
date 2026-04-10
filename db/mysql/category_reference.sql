CREATE TABLE IF NOT EXISTS `category_reference` (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    sub_category_id BIGINT NOT NULL COMMENT '子分类ID',
    type VARCHAR(255) NOT NULL COMMENT '权威参考文本类型，link/pdf',
    link VARCHAR(255) COMMENT '权威参考文本链接',
    pdf VARCHAR(255) COMMENT '权威参考文本PDF链接（OSS）',
    UNIQUE KEY uk_sub_category (sub_category_id),
    FOREIGN KEY (sub_category_id) REFERENCES sub_category(id) ON DELETE CASCADE
) COMMENT='分类权威参考文本表';
