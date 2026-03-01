.PHONY: setup dev backend frontend test eval typecheck clean deploy-backend deploy-frontend

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

# GCP Cloud Run deployment (see DEPLOY.md for setup)
deploy-backend:
	@echo "🚀 Deploying backend to Cloud Run..."
	@PROJECT_ID=$$(gcloud config get-value project) && \
	IMAGE="asia-northeast1-docker.pkg.dev/$$PROJECT_ID/cloud-run-source-deploy/cycling-backend:latest" && \
	gcloud builds submit --config=backend/cloudbuild.yaml --substitutions=_IMAGE_NAME=$$IMAGE . && \
	gcloud run deploy cycling-backend \
		--image $$IMAGE \
		--region asia-northeast1 \
		--allow-unauthenticated \
		--set-secrets=ANTHROPIC_API_KEY=anthropic-api-key:latest,ORS_API_KEY=ors-api-key:latest \
		--memory 1Gi \
		--cpu 1 \
		--timeout 300 \
		--port 8080

deploy-frontend:
	@echo "🚀 Deploying frontend to Cloud Run..."
	@if [ ! -f client/.env.production ]; then \
		echo "❌ client/.env.production not found. Create it with VITE_API_BASE_URL=<backend-url>"; \
		exit 1; \
	fi
	@PROJECT_ID=$$(gcloud config get-value project) && \
	IMAGE="asia-northeast1-docker.pkg.dev/$$PROJECT_ID/cloud-run-source-deploy/cycling-frontend:latest" && \
	gcloud builds submit --config=client/cloudbuild.yaml --substitutions=_IMAGE_NAME=$$IMAGE . && \
	gcloud run deploy cycling-frontend \
		--image $$IMAGE \
		--region asia-northeast1 \
		--allow-unauthenticated \
		--memory 512Mi \
		--cpu 1 \
		--port 8080
