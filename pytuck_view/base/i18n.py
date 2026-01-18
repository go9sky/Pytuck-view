"""国际化消息定义

按模块组织所有国际化消息，使用 I18nMessage 对象。
"""

from pytuck_view.utils.schemas import I18nMessage


class CommonI18n:
    """通用国际化消息"""

    SUCCESS = I18nMessage(zh_cn="操作成功", en_us="Operation successful")

    UNEXPECTED_ERROR = I18nMessage(
        zh_cn="[{summary}] 服务器内部错误: {error}",
        en_us="[{summary}] Internal server error: {error}",
    )


class ApiSummaryI18n:
    """API 接口摘要国际化"""

    GET_RECENT_FILES = I18nMessage(zh_cn="获取最近文件列表", en_us="Get recent files")

    DISCOVER_FILES = I18nMessage(
        zh_cn="发现数据库文件", en_us="Discover database files"
    )

    OPEN_FILE = I18nMessage(zh_cn="打开数据库文件", en_us="Open database file")

    CLOSE_FILE = I18nMessage(zh_cn="关闭数据库文件", en_us="Close database file")


class FileI18n:
    """文件管理模块国际化"""

    # 成功消息

    OPEN_FILE_SUCCESS = I18nMessage(
        zh_cn="文件打开成功", en_us="File opened successfully"
    )

    # 错误消息

    FILE_NOT_FOUND = I18nMessage(
        zh_cn="文件不存在: {path}", en_us="File not found: {path}"
    )

    CANNOT_OPEN_FILE = I18nMessage(zh_cn="无法打开文件", en_us="Cannot open file")

    OPEN_FILE_FAILED = I18nMessage(
        zh_cn="打开文件失败: {error}", en_us="Failed to open file: {error}"
    )

    PATH_NOT_EXISTS = I18nMessage(zh_cn="路径不存在", en_us="Path does not exist")

    NOT_A_DIRECTORY = I18nMessage(zh_cn="不是目录", en_us="Not a directory")

    ACCESS_DENIED = I18nMessage(
        zh_cn="无法访问该目录（权限不足）",
        en_us="Cannot access directory (permission denied)",
    )


class DatabaseI18n:
    """数据库模块国际化"""

    APP_NAME = I18nMessage(zh_cn="Pytuck-view", en_us="Pytuck-view")

    # 错误消息
    DB_NOT_OPENED = I18nMessage(
        zh_cn="数据库文件未打开", en_us="Database file not opened"
    )

    GET_TABLES_FAILED = I18nMessage(
        zh_cn="获取表列表失败: {error}", en_us="Failed to get tables: {error}"
    )

    TABLE_NOT_EXISTS = I18nMessage(
        zh_cn="表 '{table_name}' 不存在", en_us="Table '{table_name}' does not exist"
    )

    GET_SCHEMA_FAILED = I18nMessage(
        zh_cn="获取表结构失败: {error}", en_us="Failed to get schema: {error}"
    )

    GET_ROWS_FAILED = I18nMessage(
        zh_cn="获取表数据失败: {error}", en_us="Failed to get rows: {error}"
    )
