.PHONY: fmt lint typecheck test check run zipapp exe

fmt:
	uv run --group dev ruff format .

lint:
	uv run --group dev ruff check .

typecheck:
	uv run --group dev mypy pytuck_view

test:
	uv run --group dev pytest -q

check: lint typecheck test

run:
	uv run uvicorn pytuck_view.app:create_app --factory --reload --port 0

# 下面两个目标与 CLAUDE.md 中的命令保持一致。
# 具体打包实现可按你的现有脚本/流程补齐；这里先留出占位，避免“文档有命令但仓库无目标”。
zipapp:
	@echo "TODO: 实现 zipapp 打包（生成 dist/pytuck-view.pyz）"

exe:
	@echo "TODO: 实现 nuitka --onefile 打包（生成 dist/pytuck-view.exe）"
