"""
数据库服务层

提供 pytuck Storage 的统一接口
处理数据库连接、表查询、模式信息等
对于缺失的功能提供占位符和警告信息
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from pytuck import Storage, Session
    PYTUCK_AVAILABLE = True
except ImportError as e:
    print(f"警告: pytuck 库导入失败: {e}")
    PYTUCK_AVAILABLE = False


@dataclass
class TableInfo:
    """表信息数据类"""
    name: str
    row_count: int
    columns: List[Dict[str, Any]]


@dataclass
class ColumnInfo:
    """列信息数据类"""
    name: str
    type: str
    nullable: bool
    primary_key: bool


class DatabaseService:
    """数据库服务"""

    def __init__(self):
        self.storage = None
        self.session = None
        self.file_path = None

    def open_database(self, file_path: str) -> bool:
        """打开数据库文件"""
        if not PYTUCK_AVAILABLE:
            raise RuntimeError("pytuck 库不可用")

        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"数据库文件不存在: {file_path}")

            # 根据文件扩展名确定引擎类型
            engine = self._detect_engine(path_obj.suffix)

            # 创建 Storage 实例
            self.storage = Storage(
                file_path=str(path_obj),
                engine=engine,
                auto_flush=False  # 只读模式，不需要自动刷新
            )

            # 创建 Session 实例
            self.session = Session(self.storage)
            self.file_path = file_path

            return True

        except Exception as e:
            print(f"打开数据库失败: {e}")
            return False

    def _detect_engine(self, suffix: str) -> str:
        """根据文件后缀检测引擎类型"""
        engine_map = {
            '.bin': 'binary',
            '.json': 'json',
            '.csv': 'csv'
        }
        return engine_map.get(suffix.lower(), 'binary')

    def list_tables(self) -> List[str]:
        """列出所有表名"""
        if not self.storage:
            raise RuntimeError("数据库未打开")

        try:
            # 尝试获取表列表
            if hasattr(self.storage, 'tables'):
                table_names = []
                for table_name in self.storage.tables.keys():
                    table_names.append(str(table_name))  # 确保是字符串
                return table_names
            else:
                # 如果 pytuck 还没有提供表列表功能，返回占位符
                return self._get_placeholder_tables()

        except Exception as e:
            print(f"获取表列表失败: {e}")
            return self._get_placeholder_tables()

    def _get_placeholder_tables(self) -> List[str]:
        """返回占位符表列表（当 pytuck 功能不可用时）"""
        return [
            "⚠️ 表列表功能暂不可用",
            "💡 提示: 需要在 pytuck 库中添加获取表列表的方法",
            "📋 建议方法: storage.list_tables() 或 storage.get_table_names()"
        ]

    def get_table_info(self, table_name: str) -> Optional[TableInfo]:
        """获取表信息（模式和行数）"""
        if not self.storage:
            raise RuntimeError("数据库未打开")

        # 如果是占位符表名，返回占位符信息
        if table_name.startswith(('⚠️', '💡', '📋')):
            return TableInfo(
                name=table_name,
                row_count=0,
                columns=[{
                    "name": "message",
                    "type": "str",
                    "nullable": False,
                    "primary_key": False,
                    "description": "这是一个提示信息，表示该功能需要在 pytuck 库中实现"
                }]
            )

        try:
            # 尝试获取表对象
            if hasattr(self.storage, 'get_table'):
                table = self.storage.get_table(table_name)
                if table:
                    return self._extract_table_info(table, table_name)

            # 如果获取失败，返回占位符信息
            return self._get_placeholder_table_info(table_name)

        except Exception as e:
            print(f"获取表信息失败 {table_name}: {e}")
            return self._get_placeholder_table_info(table_name)

    def _extract_table_info(self, table, table_name: str) -> TableInfo:
        """从 pytuck 表对象提取信息"""
        columns = []

        try:
            # 尝试获取列信息
            if hasattr(table, 'columns') and table.columns:
                # 处理不同的列格式
                if isinstance(table.columns, dict):
                    # 字典格式的列定义
                    for col_name, col_obj in table.columns.items():
                        col_info = {
                            "name": str(col_name),
                            "type": str(getattr(col_obj, 'col_type', getattr(col_obj, 'type', 'unknown'))),
                            "nullable": bool(getattr(col_obj, 'nullable', True)),
                            "primary_key": bool(getattr(col_obj, 'primary_key', False))
                        }
                        columns.append(col_info)
                elif isinstance(table.columns, list):
                    # 数组格式的列定义（pytuck JSON 格式）
                    for col_def in table.columns:
                        if isinstance(col_def, dict):
                            col_info = {
                                "name": str(col_def.get('name', 'unknown')),
                                "type": str(col_def.get('type', 'unknown')),
                                "nullable": bool(col_def.get('nullable', True)),
                                "primary_key": bool(col_def.get('primary_key', False))
                            }
                            columns.append(col_info)

            # 尝试获取行数
            row_count = 0
            if hasattr(table, 'records') and table.records:
                # pytuck JSON 格式使用 records
                row_count = len(table.records)
            elif hasattr(table, 'data') and table.data:
                # 其他格式使用 data
                row_count = len(table.data)
            elif hasattr(self.storage, 'count_rows'):
                # 假设将来会有这个方法
                try:
                    row_count = self.storage.count_rows(table_name)
                except:
                    row_count = 0

        except Exception as e:
            print(f"提取表信息失败: {e}")
            columns = []
            row_count = 0

        return TableInfo(
            name=table_name,
            row_count=row_count,
            columns=columns if columns else self._get_placeholder_columns()
        )

    def _get_placeholder_table_info(self, table_name: str) -> TableInfo:
        """返回占位符表信息"""
        return TableInfo(
            name=table_name,
            row_count=0,
            columns=self._get_placeholder_columns()
        )

    def _get_placeholder_columns(self) -> List[Dict[str, Any]]:
        """返回占位符列信息"""
        return [{
            "name": "⚠️ 列信息不可用",
            "type": "placeholder",
            "nullable": True,
            "primary_key": False,
            "description": "需要在 pytuck 库中添加获取表结构的方法"
        }]

    def get_table_data(self, table_name: str, page: int = 1, limit: int = 50,
                       sort_by: Optional[str] = None, order: str = 'asc') -> Dict[str, Any]:
        """获取表数据（分页）"""
        if not self.storage:
            raise RuntimeError("数据库未打开")

        # 如果是占位符表名，返回占位符数据
        if table_name.startswith(('⚠️', '💡', '📋')):
            return {
                "rows": [{"message": "这是一个功能提示，实际数据需要 pytuck 库支持"}],
                "total": 1,
                "page": page,
                "limit": limit
            }

        try:
            # 计算偏移量
            offset = (page - 1) * limit

            # 尝试查询数据
            rows = []
            total = 0

            if hasattr(self.storage, 'query'):
                # 尝试使用 storage.query 方法
                try:
                    all_rows = self.storage.query(table_name, conditions=None)
                    total = len(all_rows) if all_rows else 0

                    if all_rows:
                        # 将查询结果转换为纯字典格式，确保可以序列化为 JSON
                        serializable_rows = []
                        for row in all_rows:
                            if hasattr(row, '__dict__'):
                                # 如果是对象，转换为字典
                                row_dict = {}
                                for key, value in row.__dict__.items():
                                    # 跳过私有属性和方法
                                    if not key.startswith('_') and not callable(value):
                                        row_dict[key] = self._serialize_value(value)
                                serializable_rows.append(row_dict)
                            elif isinstance(row, dict):
                                # 如果已经是字典，清理不可序列化的值
                                clean_dict = {}
                                for key, value in row.items():
                                    if not callable(value):
                                        clean_dict[key] = self._serialize_value(value)
                                serializable_rows.append(clean_dict)
                            else:
                                # 其他情况，转换为字符串表示
                                serializable_rows.append({"data": str(row)})

                        # 简单排序
                        if sort_by and serializable_rows:
                            reverse_order = order.lower() == 'desc'
                            try:
                                serializable_rows.sort(
                                    key=lambda x: x.get(sort_by, ''),
                                    reverse=reverse_order
                                )
                            except (TypeError, KeyError):
                                # 如果排序失败，保持原顺序
                                pass

                        # 分页
                        rows = serializable_rows[offset:offset + limit]
                    else:
                        rows = []

                except Exception as e:
                    print(f"查询数据失败: {e}")
                    rows = []
                    total = 0
            else:
                # 如果没有 query 方法，尝试直接访问表数据
                try:
                    table = self.storage.get_table(table_name)
                    if table:
                        # 尝试获取数据
                        table_data = None
                        if hasattr(table, 'records'):
                            table_data = table.records
                        elif hasattr(table, 'data'):
                            table_data = table.data

                        if table_data:
                            # 序列化数据
                            serializable_rows = []
                            for row in table_data:
                                clean_row = self._serialize_value(row)
                                serializable_rows.append(clean_row)

                            total = len(serializable_rows)

                            # 排序
                            if sort_by and serializable_rows:
                                reverse_order = order.lower() == 'desc'
                                try:
                                    serializable_rows.sort(
                                        key=lambda x: x.get(sort_by, '') if isinstance(x, dict) else str(x),
                                        reverse=reverse_order
                                    )
                                except (TypeError, KeyError):
                                    pass

                            # 分页
                            rows = serializable_rows[offset:offset + limit]
                        else:
                            rows = []
                            total = 0
                    else:
                        rows = []
                        total = 0
                except Exception as e:
                    print(f"直接访问表数据失败: {e}")
                    rows = []
                    total = 0

            # 如果查询失败或没有数据，返回占位符
            if not rows:
                rows = self._get_placeholder_data()
                total = 1

            return {
                "rows": rows,
                "total": total,
                "page": page,
                "limit": limit
            }

        except Exception as e:
            print(f"获取表数据失败 {table_name}: {e}")
            return {
                "rows": self._get_placeholder_data(),
                "total": 1,
                "page": page,
                "limit": limit
            }

    def _serialize_value(self, value) -> Any:
        """将值序列化为 JSON 兼容格式"""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, type):
            # 处理类型对象，如 <class 'int'>
            return value.__name__
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items() if not callable(v)}
        elif hasattr(value, '__dict__'):
            # 对象转字典
            return {k: self._serialize_value(v) for k, v in value.__dict__.items()
                   if not k.startswith('_') and not callable(v)}
        else:
            # 其他类型转字符串
            try:
                return str(value)
            except:
                return "unknown"

    def _get_placeholder_data(self) -> List[Dict[str, Any]]:
        """返回占位符数据"""
        return [{
            "id": 1,
            "message": "⚠️ 数据查询功能暂不可用",
            "suggestion": "需要在 pytuck 库中完善数据查询接口",
            "methods_needed": "storage.query() 或 session.execute(select())"
        }]

    def close(self):
        """关闭数据库连接"""
        if self.session:
            try:
                # pytuck Session 可能没有显式的 close 方法
                # 只需要清理引用
                self.session = None
            except:
                pass

        self.storage = None
        self.file_path = None

    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库基本信息"""
        if not self.storage:
            return {"error": "数据库未打开"}

        try:
            tables = self.list_tables()
            # 过滤掉占位符表名
            real_tables = [t for t in tables if not t.startswith(('⚠️', '💡', '📋'))]

            return {
                "file_path": self.file_path,
                "file_size": os.path.getsize(self.file_path) if self.file_path else 0,
                "tables_count": len(real_tables),
                "engine": getattr(self.storage, 'engine', 'unknown'),
                "status": "connected"
            }
        except Exception as e:
            return {
                "error": f"获取数据库信息失败: {e}",
                "status": "error"
            }