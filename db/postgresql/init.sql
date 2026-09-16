-- 幂等创建：仅当库不存在时才创建（\gexec 为 psql 元命令）
SELECT 'CREATE DATABASE demo'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'demo')\gexec
