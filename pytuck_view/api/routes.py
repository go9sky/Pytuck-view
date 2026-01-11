"""
API 路由模块

实现所有 REST API 端点
支持文件管理、数据库操作、表查询等功能
统一返回格式: {code: 状态码, msg: 消息, data: 数据}
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..services.file_manager import file_manager, FileRecord
from ..services.database import DatabaseService


# 创建路由器
router = APIRouter()

# 全局数据库服务实例字典（按 file_id 存储）
db_services: Dict[str, DatabaseService] = {}


# Pydantic 模型
class OpenFileRequest(BaseModel):
    """打开文件请求模型"""
    path: str


# 统一响应格式
def success_response(data: Any = None, msg: str = "操作成功") -> Dict[str, Any]:
    """成功响应格式"""
    return {"code": 200, "msg": msg, "data": data}


def error_response(code: int = 500, msg: str = "操作失败", data: Any = None) -> Dict[str, Any]:
    """错误响应格式"""
    return {"code": code, "msg": msg, "data": data}


@router.get("/recent-files")
async def get_recent_files():
    """获取最近打开的文件列表"""
    try:
        recent_files = file_manager.get_recent_files(limit=10)
        files_data = []

        for file_record in recent_files:
            files_data.append({
                "file_id": file_record.file_id,
                "path": file_record.path,
                "name": file_record.name,
                "last_opened": file_record.last_opened,
                "file_size": file_record.file_size
            })

        return success_response(data={"files": files_data}, msg="获取最近文件列表成功")

    except Exception as e:
        return error_response(code=500, msg=f"获取最近文件列表失败: {str(e)}")


@router.get("/discover-files")
async def discover_files(directory: Optional[str] = Query(None)):
    """发现指定目录中的 pytuck 文件"""
    try:
        discovered = file_manager.discover_files(directory)
        return success_response(data={"files": discovered}, msg="文件扫描成功")
    except Exception as e:
        return error_response(code=500, msg=f"文件扫描失败: {str(e)}")


@router.post("/open-file")
async def open_file(request: OpenFileRequest):
    """打开数据库文件"""
    try:
        # 使用文件管理器打开文件
        file_record = file_manager.open_file(request.path)
        if not file_record:
            return error_response(code=404, msg="无法打开文件")

        # 创建数据库服务实例
        db_service = DatabaseService()
        success = db_service.open_database(request.path)

        if not success:
            return error_response(code=500, msg="数据库打开失败")

        # 保存数据库服务实例
        db_services[file_record.file_id] = db_service

        # 获取表数量信息
        try:
            tables = db_service.list_tables()
            # 过滤掉占位符表名
            real_tables = [t for t in tables if not t.startswith(('⚠️', '💡', '📋'))]
            tables_count = len(real_tables)
        except:
            tables_count = 0

        data = {
            "file_id": file_record.file_id,
            "name": file_record.name,
            "path": file_record.path,
            "tables_count": tables_count,
            "file_size": file_record.file_size
        }

        return success_response(data=data, msg="数据库打开成功")

    except FileNotFoundError as e:
        return error_response(code=404, msg=str(e))
    except ValueError as e:
        return error_response(code=400, msg=str(e))
    except Exception as e:
        return error_response(code=500, msg=f"打开文件失败: {str(e)}")


@router.get("/tables/{file_id}")
async def get_tables(file_id: str):
    """获取指定数据库中的表列表"""
    if file_id not in db_services:
        return error_response(code=404, msg="数据库文件未打开")

    try:
        db_service = db_services[file_id]
        tables = db_service.list_tables()

        # 检查是否有占位符表
        placeholder_tables = [t for t in tables if t.startswith(('⚠️', '💡', '📋'))]
        if placeholder_tables:
            return success_response(
                data={"tables": tables, "has_placeholder": True},
                msg="表列表获取成功，但部分功能需要 pytuck 库支持"
            )
        else:
            return success_response(data={"tables": tables, "has_placeholder": False}, msg="表列表获取成功")

    except Exception as e:
        return error_response(code=500, msg=f"获取表列表失败: {str(e)}")


@router.get("/schema/{file_id}/{table_name}")
async def get_table_schema(file_id: str, table_name: str):
    """获取表结构信息"""
    if file_id not in db_services:
        return error_response(code=404, msg="数据库文件未打开")

    try:
        db_service = db_services[file_id]
        table_info = db_service.get_table_info(table_name)

        if not table_info:
            return error_response(code=404, msg=f"表 '{table_name}' 不存在")

        data = {
            "table_name": table_info.name,
            "row_count": table_info.row_count,
            "columns": table_info.columns
        }

        # 检查是否有占位符列
        placeholder_columns = [c for c in table_info.columns if c.get("name", "").startswith('⚠️')]
        if placeholder_columns:
            return success_response(
                data=data,
                msg="表结构获取成功，但列信息功能需要 pytuck 库完善"
            )
        else:
            return success_response(data=data, msg="表结构获取成功")

    except Exception as e:
        return error_response(code=500, msg=f"获取表结构失败: {str(e)}")


@router.get("/rows/{file_id}/{table_name}")
async def get_table_rows(
    file_id: str,
    table_name: str,
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    limit: int = Query(50, ge=1, le=1000, description="每页行数，最大 1000"),
    sort: Optional[str] = Query(None, description="排序字段"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="排序方向")
):
    """获取表数据（分页）"""
    if file_id not in db_services:
        return error_response(code=404, msg="数据库文件未打开")

    try:
        db_service = db_services[file_id]
        data = db_service.get_table_data(
            table_name=table_name,
            page=page,
            limit=limit,
            sort_by=sort,
            order=order
        )

        # 检查是否是占位符数据
        if (data.get("rows") and len(data["rows"]) > 0 and
            isinstance(data["rows"][0], dict) and
            "⚠️" in str(data["rows"][0].get("message", ""))):
            return success_response(
                data=data,
                msg="数据查询功能暂不可用，需要 pytuck 库支持"
            )
        else:
            return success_response(data=data, msg="表数据获取成功")

    except Exception as e:
        return error_response(code=500, msg=f"获取表数据失败: {str(e)}")


@router.delete("/close-file/{file_id}")
async def close_file(file_id: str):
    """关闭数据库文件"""
    try:
        # 关闭数据库服务
        if file_id in db_services:
            db_services[file_id].close()
            del db_services[file_id]

        # 从文件管理器中移除
        file_manager.close_file(file_id)

        return success_response(msg="文件已关闭")

    except Exception as e:
        return error_response(code=500, msg=f"关闭文件失败: {str(e)}")


@router.get("/database-info/{file_id}")
async def get_database_info(file_id: str):
    """获取数据库基本信息"""
    if file_id not in db_services:
        return error_response(code=404, msg="数据库文件未打开")

    try:
        db_service = db_services[file_id]
        info = db_service.get_database_info()

        if "error" in info:
            return error_response(code=500, msg=info["error"])

        return success_response(data=info, msg="数据库信息获取成功")

    except Exception as e:
        return error_response(code=500, msg=f"获取数据库信息失败: {str(e)}")


@router.get("/status")
async def get_status():
    """获取服务状态"""
    data = {
        "service": "pytuck-view",
        "version": "25.1.0",
        "open_databases": len(db_services),
        "status": "running"
    }
    return success_response(data=data, msg="服务状态正常")