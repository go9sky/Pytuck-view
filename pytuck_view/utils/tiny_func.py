import traceback
from pathlib import Path


def simplify_exception(err: Exception) -> str:
    """简化错误日志"""
    msg = "".join(traceback.format_exception(err)).replace(str(Path.cwd()), "")
    return f"{err.__class__.__name__}: {err}\nAt: \n{msg}"
