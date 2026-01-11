"""
FastAPI 应用工厂

创建和配置 FastAPI 应用实例
挂载静态文件、模板和路由
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

from .api.routes import router as api_router


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""

    app = FastAPI(
        title="pytuck-view",
        description="轻量级 pytuck 数据库可视化工具",
        version="25.1.0",
        docs_url=None,  # 禁用自动文档以减小体积
        redoc_url=None,
    )

    # 获取当前目录路径
    current_dir = Path(__file__).parent

    # 挂载静态文件
    static_path = current_dir / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # 设置模板
    templates_path = current_dir / "templates"
    if templates_path.exists():
        templates = Jinja2Templates(directory=str(templates_path))
    else:
        templates = None

    # 注册 API 路由
    app.include_router(api_router, prefix="/api")

    # 根路径路由 - 返回主页面
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """返回主页面"""
        if templates:
            return templates.TemplateResponse("index.html", {"request": request})
        else:
            # 如果模板不存在，返回简单的 HTML
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>pytuck-view</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>pytuck-view 正在加载...</h1>
                <p>模板文件尚未创建。</p>
            </body>
            </html>
            """)

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {"status": "ok", "service": "pytuck-view"}

    return app