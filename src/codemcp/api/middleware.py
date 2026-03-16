"""
FastAPI 中间件

CORS、请求日志、异常处理等中间件。
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from ..config import settings
from ..exceptions import CodeMCPError


def setup_middleware(app: FastAPI) -> None:
    """设置中间件

    Args:
        app: FastAPI 应用实例
    """

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # 可信主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # 生产环境应限制
    )

    # GZip 压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> Response:
        """记录请求日志"""
        start_time = time.time()

        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"

        # 执行请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录日志
        log_data = {
            "method": method,
            "url": url,
            "client_ip": client_ip,
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s",
            "user_agent": request.headers.get("user-agent", ""),
        }

        # 根据状态码选择日志级别
        if response.status_code >= 500:
            app.state.logger.error("Server error", extra=log_data)
        elif response.status_code >= 400:
            app.state.logger.warning("Client error", extra=log_data)
        else:
            app.state.logger.info("Request processed", extra=log_data)

        # 添加响应头
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        response.headers["X-API-Version"] = "v1"

        return response

    # 全局异常处理中间件
    @app.middleware("http")
    async def handle_exceptions(request: Request, call_next: Callable) -> Response:
        """处理全局异常"""
        try:
            return await call_next(request)
        except CodeMCPError as e:
            # 处理自定义异常
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "message": str(e),
                    "type": e.__class__.__name__,
                },
            )
        except Exception as e:
            # 处理未捕获的异常
            app.state.logger.exception("Unhandled exception")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "type": e.__class__.__name__,
                },
            )