# 后端镜像：FastAPI + uvicorn。
# 构建上下文为仓库根目录（需要同时拿到 backend/ 与 data_source/）。
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

# 先装依赖（利用层缓存）
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 拷贝代码与 seed 脚本
COPY backend/app /app/backend/app
COPY backend/scripts /app/backend/scripts

# 拷贝数据源（首次启动 seed 用；seed 后 DB 持久化在 volume，不再依赖这些文件）
COPY data_source /app/data_source

# SQLite 数据目录（挂载为命名 volume 以持久化）
RUN mkdir -p /app/backend/data
VOLUME /app/backend/data

EXPOSE 8000

COPY backend/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
