#!/usr/bin/env python3
"""
pytuck-view 应用入口点

启动 uvicorn 服务器并自动打开浏览器
使用随机端口，确保零冲突
"""

import os
import sys
import webbrowser
import socket
import time
import threading
from contextlib import asynccontextmanager

import uvicorn


def find_free_port() -> int:
    """找到一个可用的端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def open_browser(url: str, delay: float = 1.5):
    """延迟打开浏览器，确保服务器已启动"""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"无法自动打开浏览器: {e}")
            print(f"请手动访问: {url}")

    threading.Thread(target=_open, daemon=True).start()


@asynccontextmanager
async def lifespan(app):
    """应用生命周期管理"""
    print("🚀 pytuck-view 正在启动...")
    yield
    print("👋 pytuck-view 正在关闭...")


def main():
    """主入口函数"""
    try:
        # 查找可用端口
        port = find_free_port()
        url = f"http://localhost:{port}"

        print(f"📊 pytuck-view v{__import__('pytuck_view').__version__}")
        print(f"🌐 服务器启动在: {url}")
        print("按 Ctrl+C 停止服务器")

        # 延迟打开浏览器
        open_browser(url)

        # 启动 uvicorn 服务器
        uvicorn.run(
            "pytuck_view.app:create_app",
            factory=True,
            host="127.0.0.1",
            port=port,
            access_log=False,  # 减少日志输出，保持简洁
            log_level="warning",  # 只显示警告和错误
        )

    except KeyboardInterrupt:
        print("\n✨ 感谢使用 pytuck-view!")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()