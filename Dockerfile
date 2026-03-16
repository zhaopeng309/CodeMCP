# CodeMCP Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 构建阶段
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml ./

# 安装构建工具和依赖
RUN pip install --upgrade pip && \
    pip install build && \
    python -m build --wheel

# 运行阶段
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 codemcp && \
    chown -R codemcp:codemcp /app

# 从构建阶段复制wheel包
COPY --from=builder /app/dist/*.whl /tmp/

# 安装应用
RUN pip install --no-cache-dir /tmp/*.whl

# 复制应用代码和配置文件
COPY --chown=codemcp:codemcp .env.example .env.example
COPY --chown=codemcp:codemcp alembic.ini .
COPY --chown=codemcp:codemcp src/ ./src/

# 创建数据目录
RUN mkdir -p /data && chown codemcp:codemcp /data

# 切换到非root用户
USER codemcp

# 环境变量
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:////data/codemcp.db

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/status')" || exit 1

# 默认命令：启动服务器
CMD ["codemcp-server", "--host", "0.0.0.0", "--port", "8000"]

# 可选命令：
# 1. 启动CLI: CMD ["codemcp", "--help"]
# 2. 运行迁移: CMD ["alembic", "upgrade", "head"] && ["codemcp-server", "--host", "0.0.0.0", "--port", "8000"]