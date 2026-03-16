#!/usr/bin/env python3
"""
测试 CodeMCP API 服务器
"""

import asyncio
import httpx
import time
import sys

async def test_api():
    """测试 API 服务器"""
    print("测试 CodeMCP API 服务器...")
    
    # 启动服务器（在后台）
    import subprocess
    import os
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__)) + ":" + env.get("PYTHONPATH", "")
    
    # 启动服务器进程
    server_process = subprocess.Popen(
        ["python", "-m", "codemcp.api.server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print("等待服务器启动...")
    time.sleep(3)  # 等待服务器启动
    
    try:
        # 测试健康检查端点
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试根端点
            print("测试根端点...")
            response = await client.get("http://localhost:8000/")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            
            # 测试健康检查端点
            print("\n测试健康检查端点...")
            response = await client.get("http://localhost:8000/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            
            # 测试系统API端点
            print("\n测试系统API端点...")
            response = await client.get("http://localhost:8000/api/v1/systems/")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        # 停止服务器
        print("\n停止服务器...")
        server_process.terminate()
        server_process.wait()
        print("服务器已停止")

if __name__ == "__main__":
    asyncio.run(test_api())