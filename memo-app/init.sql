-- ============================================
-- 读书摘抄检索系统 - 数据库初始化脚本
-- 使用方法: mysql -u root -p < init.sql
-- ============================================

DROP DATABASE IF EXISTS memo_db;
CREATE DATABASE memo_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE memo_db;

-- 创建专用用户（如已存在则跳过）
CREATE USER IF NOT EXISTS 'memo'@'localhost' IDENTIFIED BY 'memopass';
CREATE USER IF NOT EXISTS 'memo'@'%' IDENTIFIED BY 'memopass';
GRANT ALL PRIVILEGES ON memo_db.* TO 'memo'@'localhost';
GRANT ALL PRIVILEGES ON memo_db.* TO 'memo'@'%';
FLUSH PRIVILEGES;

-- 书籍表
CREATE TABLE IF NOT EXISTS books (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '书籍ID',
    title VARCHAR(255) NOT NULL COMMENT '书名',
    author VARCHAR(255) DEFAULT '' COMMENT '作者',
    cover VARCHAR(500) DEFAULT '' COMMENT '封面图片URL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_title_author (title, author)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='书籍表';

-- 摘抄表
CREATE TABLE IF NOT EXISTS excerpts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '摘抄ID',
    book_id INT UNSIGNED NOT NULL COMMENT '所属书籍',
    content TEXT COMMENT '摘抄原文',
    insights TEXT COMMENT '个人想法/评论',
    links JSON DEFAULT (JSON_ARRAY()) COMMENT '链接数组',
    images JSON DEFAULT (JSON_ARRAY()) COMMENT '图片URL数组',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FULLTEXT INDEX ft_excerpt (content, insights) WITH PARSER ngram,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='摘抄主表';

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '标签ID',
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '标签名',
    color VARCHAR(7) DEFAULT '#409EFF' COMMENT '标签颜色(hex)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='标签表';

-- 摘抄-标签关联表
CREATE TABLE IF NOT EXISTS excerpt_tags (
    excerpt_id BIGINT UNSIGNED NOT NULL,
    tag_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (excerpt_id, tag_id),
    FOREIGN KEY (excerpt_id) REFERENCES excerpts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='摘抄标签关联表';

-- 预置标签
INSERT INTO tags (name, color) VALUES
    ('哲学', '#409EFF'),
    ('心理学', '#67C23A'),
    ('文学', '#E6A23C'),
    ('金句', '#F56C6C'),
    ('方法论', '#909399'),
    ('待整理', '#9254DE')
ON DUPLICATE KEY UPDATE color=VALUES(color);

SELECT '数据库 memo_db 初始化完成（读书摘抄系统）' AS status;
