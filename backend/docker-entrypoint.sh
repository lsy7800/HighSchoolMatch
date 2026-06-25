#!/bin/sh
# 容器启动入口：首次运行时自动 seed 数据库，之后直接启动 uvicorn。
set -e

DB_PATH=/app/backend/data/app.db

if [ ! -f "$DB_PATH" ]; then
  echo "[entrypoint] 未发现现有数据库，开始首次 seed ..."
  python -m scripts.seed_2025
  echo "[entrypoint] seed 完成。"
else
  echo "[entrypoint] 数据库已存在，跳过 seed。"
fi

echo "[entrypoint] 启动服务：$@"
exec "$@"
