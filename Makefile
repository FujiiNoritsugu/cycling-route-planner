.PHONY: setup dev backend frontend test eval typecheck clean

setup:
	cp .env.example .env
	@echo "⚠️  .env を編集して API キーを設定してください"
	cd backend && uv sync
	cd planner && uv sync
	cd eval && uv sync
	cd client && npm install

dev:
	@echo "🚴 バックエンド + フロントエンド起動..."
	@if command -v tmux >/dev/null 2>&1; then \
		tmux new-session -d -s cycling \
			'cd backend && PYTHONPATH=$(PWD):$$PYTHONPATH uv run uvicorn app.main:app --reload --port 8080' \; \
			split-window -h \
			'cd client && npm run dev' \; \
			select-layout even-horizontal; \
		tmux attach -t cycling; \
	else \
		echo "tmux がないため backend のみ起動します"; \
		echo "別ターミナルで make frontend を実行してください"; \
		cd backend && PYTHONPATH=$(PWD):$$PYTHONPATH uv run uvicorn app.main:app --reload --port 8080; \
	fi

backend:
	cd backend && PYTHONPATH=$(PWD):$$PYTHONPATH uv run uvicorn app.main:app --reload --port 8080

frontend:
	cd client && npm run dev

test:
	cd backend && uv run pytest -v
	cd planner && uv run pytest -v
	cd client && npm test

eval:
	cd eval && uv run python -m src.evaluate

typecheck:
	cd backend && uv run mypy app/
	cd planner && uv run mypy pipeline/

clean:
	rm -rf backend/.venv planner/.venv eval/.venv client/node_modules
	rm -rf data/
