"""
Gateway 服务器

FastAPI 应用创建和配置。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from .. import __version__
from ..config import settings
from ..database.session import close_db, init_db
from .middleware import setup_middleware
from .routes import api_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("codemcp.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    logger.info("Starting CodeMCP Gateway server...")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Debug mode: {settings.debug}")

    # 初始化数据库
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    # 添加 logger 到 app.state
    app.state.logger = logger

    yield

    # 关闭事件
    logger.info("Shutting down CodeMCP Gateway server...")
    await close_db()


def create_app() -> FastAPI:
    """创建 FastAPI 应用

    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(
        title="CodeMCP Gateway API",
        description="CodeMCP - AI协同编排与执行服务器的 Gateway API",
        version=__version__,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # 设置中间件
    setup_middleware(app)

    # 健康检查端点
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": "codemcp-gateway",
            "version": __version__,
        }

    @app.get("/", tags=["root"])
    async def root() -> dict:
        """根端点"""
        return {
            "message": "Welcome to CodeMCP Gateway API",
            "docs": "/docs" if settings.debug else "disabled",
            "version": __version__,
        }

    # 包含 API 路由
    app.include_router(api_router, prefix=settings.api_prefix)

    # 自定义 OpenAPI 文档
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # 自定义文档信息
        openapi_schema["info"]["contact"] = {
            "name": "CodeMCP Team",
            "email": "team@codemcp.example.com",
        }
        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    return app


# 创建应用实例
app = create_app()


def main() -> None:
    """主函数，用于命令行启动"""
    import uvicorn

    uvicorn.run(
        "codemcp.api.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()