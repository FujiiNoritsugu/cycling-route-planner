# Cycling Route AI Planner

出発地・目的地・好みを入力すると、地図・天気・路面情報を総合的に判断し、LLM（Claude）が最適なサイクリングルートを提案するWebアプリ。

## 技術スタック

- **LLM**: Anthropic Claude API (claude-sonnet-4-5-20250929)
- **地図**: OpenRouteService API（ルート生成・標高プロファイル）
- **天気**: OpenMeteo API（無料、APIキー不要）
- **サーバー**: FastAPI + Uvicorn
- **フロント**: React + TypeScript + Tailwind CSS + Leaflet（地図表示）
- **Python パッケージ管理**: uv / pip
- **テスト**: pytest + vitest

## プロジェクト構成

```
cycling-route-planner/
├── backend/              # FastAPI サーバー
│   ├── app/
│   │   ├── main.py              # FastAPI アプリ + CORS
│   │   ├── schemas.py           # Pydantic モデル（全チーム共通）
│   │   ├── database.py          # SQLite 履歴管理
│   │   ├── routers/
│   │   │   ├── plan.py          # POST /api/plan (SSE)
│   │   │   ├── weather.py       # GET /api/weather
│   │   │   └── history.py       # GET /api/history
│   │   └── services/
│   │       ├── claude.py        # Claude API ストリーミング
│   │       └── streaming.py     # SSE ユーティリティ
│   ├── tests/
│   │   └── test_api.py          # 統合テスト (12/12 passing)
│   ├── pyproject.toml
│   └── requirements.txt
│
├── planner/              # ルート生成パイプライン
│   ├── route_generator.py       # OpenRouteService API
│   ├── weather_client.py        # OpenMeteo API
│   ├── elevation.py             # 標高プロファイル
│   ├── analyzer.py              # Claude コンテキスト構築
│   ├── risk_assessor.py         # リスク評価・装備推奨
│   └── tests/                   # ユニットテスト (66/66 passing)
│
├── client/               # React フロントエンド
│   ├── src/
│   │   ├── types.ts             # TypeScript 型定義
│   │   ├── components/
│   │   │   ├── RouteMap.tsx     # Leaflet 地図表示
│   │   │   ├── PlanForm.tsx     # ルート設定フォーム
│   │   │   ├── WeatherPanel.tsx # 天気タイムライン
│   │   │   ├── AnalysisPanel.tsx # LLM 分析表示
│   │   │   └── ElevationChart.tsx # 標高グラフ
│   │   ├── hooks/
│   │   │   └── usePlan.ts       # SSE ストリーミング
│   │   └── App.tsx
│   ├── vite.config.ts           # /api プロキシ設定
│   └── package.json
│
└── eval/                 # 品質評価
    ├── test_routes.json         # テストケース 5件
    ├── evaluate.py              # LLM-as-Judge 評価
    └── bench_api.py             # パフォーマンス計測
```

## セットアップ

### 1. 環境変数設定

```bash
# backend/.env を作成
cp backend/.env.example backend/.env

# 以下のAPIキーを設定
# ANTHROPIC_API_KEY=sk-ant-...
# OPENROUTESERVICE_API_KEY=your-ors-key
```

### 2. バックエンドセットアップ

```bash
cd backend

# Python 仮想環境作成
python3 -m venv .venv
source .venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt

# テスト実行
pytest tests/ -v

# 型チェック
mypy app/ --strict
```

### 3. フロントエンドセットアップ

```bash
cd client

# 依存パッケージインストール
npm install

# 開発サーバー起動
npm run dev

# ビルド
npm run build
```

### 4. プランナーモジュールセットアップ

```bash
cd planner

# テスト実行
python3 -m pytest tests/ -v
```

## 起動方法

### バックエンド起動

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8080
またはプロジェクトルートで
make backend

```

- サーバー: http://127.0.0.1:8080
- Swagger UI: http://127.0.0.1:8080/docs
- ReDoc: http://127.0.0.1:8080/redoc

### フロントエンド起動（別ターミナル）

```bash
cd client
npm run dev
```

- フロントエンド: http://localhost:5173
- `/api` は `localhost:8080` にプロキシされます

## API エンドポイント

### POST /api/plan
ルート生成リクエスト → LLMが分析してルート提案（SSEストリーミング）

**Request:**
```json
{
  "origin": {"lat": 34.573, "lng": 135.483, "name": "堺市上野芝"},
  "destination": {"lat": 34.396, "lng": 135.757, "name": "吉野山"},
  "preferences": {
    "difficulty": "moderate",
    "avoid_traffic": true,
    "prefer_scenic": true,
    "max_distance_km": 100,
    "max_elevation_gain_m": 1500
  },
  "departure_time": "2025-03-15T07:00:00"
}
```

**Response:** SSE stream
- `event: route_data` → ルート座標・標高データ
- `event: weather` → 天気予報データ
- `event: token` → LLMの分析テキスト（ストリーミング）
- `event: done` → 完了

### GET /api/weather
指定地点の天気予報取得

**Request:**
```
GET /api/weather?lat=34.6&lng=135.5&date=2025-03-15
```

**Response:**
```json
{
  "data": {
    "time": "2025-03-15T00:00:00",
    "temperature": 20.0,
    "wind_speed": 4.0,
    "wind_direction": 135.0,
    "precipitation_probability": 15.0,
    "weather_code": 1,
    "description": "晴れ時々曇り"
  }
}
```

### GET /api/history
過去のルート提案履歴

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "segments": [...],
      "total_distance_km": 85.3,
      "total_elevation_gain_m": 1200,
      "llm_analysis": "...",
      "warnings": ["強風警告: 最大風速12.5m/s"],
      "recommended_gear": ["ヘルメット", "レインウェア", ...],
      "created_at": "2025-03-15T07:00:00"
    }
  ]
}
```

## テスト実行

### バックエンド

```bash
cd backend
source .venv/bin/activate

# 全テスト実行
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=app --cov-report=html

# 型チェック
mypy app/ --strict

# リント
ruff check backend/
```

**結果:** 12/12 tests passing, 84% coverage

### プランナー

```bash
cd planner

# テスト実行
python3 -m pytest tests/ -v
```

**結果:** 66/66 tests passing

### フロントエンド

```bash
cd client

# テスト実行
npm run test

# ビルドチェック
npm run build
```

## 評価システム

### ルート品質評価

```bash
cd eval

# LLM-as-Judge 評価
export ANTHROPIC_API_KEY="sk-ant-..."
python evaluate.py
```

評価軸:
1. 安全性 (1-10点): 交通量、路面状態、リスク評価の適切性
2. 天気対応 (1-10点): 天気情報の活用、警告の適切性
3. 実用性 (1-10点): 距離・時間の妥当性、補給ポイント提案
4. ユーザー満足度 (1-10点): 好みへの対応、アドバイスの質
5. 総合評価 (1-10点)

### パフォーマンス計測

```bash
cd eval

# バックエンド起動後
python bench_api.py --iterations 10
```

計測項目:
- TTFB (Time To First Byte) - ストリーミング開始時間
- 完了までの総時間
- P50 / P95 / P99 レイテンシ
- 成功率

## テストケース

`eval/test_routes.json` には以下の5つのテストケースが含まれています:

1. **堺市上野芝 → 吉野山** - ロングライド、山岳
2. **堺 → 六甲山** - ヒルクライム
3. **大和川サイクリングロード往復** - 初心者向け平坦
4. **堺 → 暗峠** - 激坂チャレンジ
5. **大阪 → 琵琶湖** - 超ロングライド

## 実装状況

### ✅ 完了
- **Backend**: FastAPI + Claude API統合 (12/12 tests passing)
- **Planner**: ルート生成パイプライン (66/66 tests passing)
- **Frontend**: React + Leaflet UI (ビルド成功)
- **Evaluator**: 品質評価システム

### コード品質
- **型安全性**: mypy strict mode 完全対応
- **テストカバレッジ**: backend 84%, planner 100%
- **リント**: ruff フォーマット適用済み
- **ドキュメント**: Google style docstring

## ライセンス

MIT License

## 開発者向けドキュメント

詳細な実装ドキュメントは各ディレクトリの README.md を参照してください:

- [backend/README.md](backend/README.md) - API サーバー実装
- [planner/README.md](planner/README.md) - ルート生成パイプライン
- [eval/README.md](eval/README.md) - 評価システム
