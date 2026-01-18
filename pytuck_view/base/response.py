"""统一响应装饰器

提供 @api_response 装饰器，自动处理异常捕获、消息翻译和响应格式化。
"""

import functools
from collections.abc import Callable, Coroutine
from inspect import iscoroutinefunction
from typing import Any, TypeVar

from pytuck_view.base.context import current_context
from pytuck_view.base.exceptions import (
    AppException,
    ServiceException,
    ValidationException,
    ResultWarningException,
)
from pytuck_view.base.i18n import CommonI18n
from pytuck_view.base.schemas import ApiResponse, fail, ok
from pytuck_view.utils.logger import logger
from pytuck_view.utils.schemas import I18nMessage
from pytuck_view.utils.tiny_func import simplify_exception

T = TypeVar("T")


def get_current_lang() -> str:
    """获取当前请求的语言

    从 ContextVar 中获取语言设置，默认返回中文。

    :return: 语言代码（如 'zh_cn', 'en_us'）
    """
    try:
        context = current_context.get()
        return context.language
    except LookupError:
        return "zh_cn"


def api_response(
    func: Callable[..., T | Coroutine[Any, Any, T]],
) -> Callable[..., ApiResponse | Coroutine[Any, Any, ApiResponse]]:
    """API 响应装饰器

    自动处理：
    1. 捕获异常并翻译消息
    2. 统一响应格式（ApiResponse）
    3. 错误日志记录

    使用示例::

        @router.get("/api/files")
        @api_response
        async def get_files(file_id: str):
            if file_id not in db_services:
                raise ServiceException(
                    DatabaseI18n.DB_NOT_OPENED,
                    file_id=file_id
                )
            return {"files": [...]}

    :param func: 要装饰的函数
    :return: 装饰后的函数
    """

    if iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> ApiResponse:
            try:
                data = await func(*args, **kwargs)
                return ok(data=data)
            except ValidationException as e:
                lang = get_current_lang()
                msg = e.translate(lang)
                return fail(msg=msg, data=e.data, code=2)
            except ServiceException as e:
                lang = get_current_lang()
                msg = e.translate(lang)
                return fail(msg=msg, data=e.data, code=1)
            except AppException as e:
                lang = get_current_lang()
                msg = e.translate(lang)
                return fail(msg=msg, data=e.data, code=1)
            except Exception as e:
                logger.error(f"未预期的错误: {func.__name__}", exc_info=e)
                return fail(msg=f"服务器内部错误: {str(e)}", code=1)

        return async_wrapper
    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> ApiResponse:
            try:
                data = func(*args, **kwargs)
                return ok(data=data)
            except ValidationException as e:
                lang = get_current_lang()
                msg = e.translate(lang)
                return fail(msg=msg, data=e.data, code=2)
            except ServiceException as e:
                lang = get_current_lang()
                msg = e.translate(lang)
                return fail(msg=msg, data=e.data, code=1)
            except AppException as e:
                lang = get_current_lang()
                msg = e.translate(lang)
                return fail(msg=msg, data=e.data, code=1)
            except Exception as e:
                logger.error(f"未预期的错误: {func.__name__}", exc_info=e)
                return fail(msg=f"服务器内部错误: {str(e)}", code=1)

        return wrapper


class ResponseUtil[T]:
    """
    返回 json 结果组装

    装饰器用法示例::

        # 使用 I18nMessage 对象，`[User]` 可以不写
        @ResponseUtil[User](i18n_summary=UserI18n.API_CREATE)
        async def create_user():
            # 不需要写 try... except
            # 返回 pydantic 模型实例，或者任意数据（None/bool/str/dict等），不能返回非数据对象（如文件对象）
            return User(id=1, name='张三')

    """

    @staticmethod
    def success[R](data: R | None = None, msg="success") -> ApiResponse[R]:
        """成功响应"""
        return ApiResponse(data=data, msg=msg, code=0)

    @staticmethod
    def fail[R](msg: str, code=1, data: R | None = None) -> ApiResponse[R]:
        """失败响应"""
        return ApiResponse(msg=msg, code=code, data=data)

    @staticmethod
    def warning[R](msg: str, code=2, data: R | None = None) -> ApiResponse[R]:
        """警告响应"""
        return ApiResponse(msg=msg, code=code, data=data)

    @staticmethod
    def error[R](msg: str, code=-1, data: R | None = None) -> ApiResponse[R]:
        """错误响应

        :param msg: 消息内容
        :param code: 响应码
        :param data: 响应数据，任何数据
        :return: 构建的响应结构模型实例
        """
        return ApiResponse(msg=msg, code=code, data=data)

    def __init__(self, i18n_summary: I18nMessage):
        """
        返回结果装饰器，将返回值统一为ApiResponse。

        - 正常返回时，应返回一个结果值作为data，返回 success（code=0）。

        发生错误时依次捕获：
            - 发生 ResultWaringException 时，直接根据该错误承载的 i18n 信息返回 waring（code=2）。
            - 发生 AppException 时，直接根据该错误承载的 i18n 信息返回 error（code=1）。
            - 发生其他 Exception 时，返回 error（code=1），记录日志，返回固定格式的国际化。

        :param i18n_summary: 接口操作名称的国际化对象
        """
        assert isinstance(i18n_summary, I18nMessage), "i18n_summary 参数必须是 I18nMessage 对象"
        self.i18n_summary = i18n_summary
        self.__lang = ""
        self.__summary = ""

    @property
    def lang(self) -> str:
        """获取当前语言"""
        if not self.__lang:
            self.__lang = get_current_lang()
        return self.__lang

    @property
    def summary(self):
        """获取 summary"""
        if not self.__summary:
            self.__summary = self.i18n_summary.get(self.lang)
        return self.__summary

    def translate_exception(self, e: AppException) -> str:
        """异常消息翻译方法"""
        return e.translate(self.lang)

    def translate_unexpected_error(self, e: Exception) -> str:
        """未预期错误消息翻译方法"""
        return CommonI18n.UNEXPECTED_ERROR.format(
            self.lang, error=str(e), summary=self.summary
        )

    def __call__(
        self, func: Callable[..., T | Coroutine[Any, Any, T]]
    ) -> Callable[..., ApiResponse | Coroutine[Any, Any, ApiResponse]]:
        """装饰器主逻辑：自动实现国际化、错误捕获、日志记录"""
        # 异步方法
        if iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> ApiResponse:
                try:
                    result = await func(*args, **kwargs)
                    return self.success(data=result)
                except ResultWarningException as e:
                    return self.warning(msg=self.translate_exception(e), data=e.data)
                except AppException as e:
                    return self.fail(msg=self.translate_exception(e), data=e.data)
                except Exception as e:
                    logger.error(
                        f"{self.summary} 发生预期之外的错误：\n{simplify_exception(e)}"
                    )
                    return self.error(self.translate_unexpected_error(e))

            return async_wrapper

        # 同步方法
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return self.success(data=result)
            except ResultWarningException as e:
                return self.warning(msg=self.translate_exception(e), data=e.data)
            except AppException as e:
                return self.error(msg=self.translate_exception(e), data=e.data)
            except Exception as e:
                logger.error(
                    f"{self.summary} 发生预期之外的错误：\n{simplify_exception(e)}"
                )
                return self.error(self.translate_unexpected_error(e))

        return wrapper
