# pytuck-view / Claude-Code 开发手册

## 项目一句话
给 pytuck 本地数据库一个“一眼看完”的轻量浏览器界面——零配置、零依赖（安装级零感知）、双击即跑。

## 核心定位
- **附属小工具**：生命周期随用随关，不抢 pytuck 核心风头。
- **纯本地**：不联网、无账号、不存储配置、不留日志。
- **单文件可携**：zipapp ≤ 2 MB，nuitka --onefile ≤ 8 MB。
- **前后端一体**：单进程、随机端口、自动开浏览器；代码层面路由与静态分层，未来可秒拆远程。

## 技术选型（冻结）
| 组件 | 选型 | 版本锁定 | 理由 |
|---|---|---|---|
| 后端 | FastAPI | `>=0.110,<1` | 开发快、异步预留、纯 Python |
| 服务器 | uvicorn | `>=0.20` | 同样纯 Python，Windows 无编译 |
| 模板 | Jinja2 | 随 FastAPI 间接依赖 | 语法熟悉、可内嵌 |
| 前端 | vue.min.js | 3.x 单文件落盘 | 体积小、响应式、与“view”谐音 |
| UI 框架 | 无 | 原生 HTML + 少量 CSS | 避免打包体积爆炸 |
| 代码风格 | Black + isort | 默认线长 88 | 提交前 `make fmt` |
| 最低 Python | 3.8 | 兼容多数系统自带 |

## 目录规范
```
pytuck_view/
 ├─ __main__.py         # 唯一入口：uvicorn.run + 浏览器自启
 ├─ app.py              # FastAPI 工厂，挂 static、templates、路由
 ├─ api/
 │   ├─ __init__.py
 │   └─ routes.py       # 所有 /api/* 端点
 ├─ static/             # 纯静态，vue.min.js 必须本地落盘
 ├─ templates/          # 仅 index.html 入口模板
 ├─ vendor/             # 可选内嵌 jinja2/markupsafe 源码，实现真·零 pip 依赖
 └─ tests/              # 用 pytest，不依赖外部服务
```
> 新增文件先问自己：用户需要多下载多少 KB？> 50 KB 需写理由。

## 运行/调试
```bash
# 开发热重载
uvicorn pytuck_view.app:create_app --factory --reload --port 0

# 一键打包
make zipapp   # 生成 dist/pytuck-view.pyz
make exe      # nuitka --onefile，生成 dist/pytuck-view.exe
```

## API 设计原则
1. 只暴露“读 + 点改”：  
   `GET  /api/tables` → 列表  
   `GET  /api/rows/{table}` → 分页数据  
   `POST /api/row/{table}/{pk}` → 单行编辑（事务短）
2. 所有接口 JSON，状态码遵守 HTTP 语义。
3. 出错时 `{"detail": "人类可读原因"}`，前端直接 `alert(detail)`。

## 前端约定
- 不写 `.vue` 单文件，直接 `index.html` 内嵌 `<script>`，减少构建链。
- 静态资源路径全部 `/static/...`，方便以后 CDN 替换。
- 样式用 `<style scoped>` 写在组件旁，总 CSS ≤ 20 KB。
- 网络请求封装成 `async function api(path, body=null)`，统一错误弹窗。

## 体积红线
- 整个 wheel ≤ 2 MB；
- 独立 exe ≤ 10 MB；
- PR 若增加 > 100 KB，CI 自动贴体积 diff 并 require review。

## 兼容性承诺
- 支持 pytuck 最新两个小版本；
- 浏览器支持 Chromium 70+（Win10 自带 Edge）、Firefox 63+；
- 不依赖浏览器插件、不依赖 ES2020 以后语法。

## 发布流程
1. 版本号跟随 **日历月**：`25.1.0`（2025 年 1 月），bugfix 第三位递增。
2. tag 即发布：git push origin 25.1.0 → GitHub Action 自动 build wheel / exe → PyPI。
3. 写 Release Notes ≤ 3 行：新增、修复、体积变化。

## 禁止清单
- ❌ 不引入新的 C 扩展、不依赖系统库。
- ❌ 不在用户目录写配置/缓存（除非一次性临时文件，退出即删）。
- ❌ 不在前端调用外部 CDN（vue.min.js 必须随包）。
- ❌ 不增加账号、登录、权限、多语言、主题切换等任何“可配置”功能。
- ❌ 不在主包 import 时执行耗时逻辑（连 DB 等），延迟到首次请求。

## Claude-Code 助手要求
- **始终使用中文回答**：与用户的所有交互、代码注释、文档说明均使用中文。
- **技术术语适度保留英文**：如 FastAPI、JSON、HTTP、Vue.js 等可保持英文，但解释说明用中文。
- **代码注释中文化**：Python 代码中的注释、文档字符串使用中文编写。

## 一句话自检
每次 commit 前问自己：
**"用户能不能 `pip install pytuck-view` 后 5 秒内看到表数据？"**
如果不能，回炉。