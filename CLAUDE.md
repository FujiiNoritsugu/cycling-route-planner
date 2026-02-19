# Cycling Route AI Planner

## 概要
出発地・目的地・好みを入力すると、地図・天気・路面情報を総合的に判断し、
LLM（Claude）が最適なサイクリングルートを提案するWebアプリ。

## 技術スタック
- LLM: Anthropic Claude API (claude-sonnet-4-5-20250929)
- 地図: OpenRouteService API（ルート生成・標高プロファイル）
- 天気: OpenMeteo API（無料、キー不要）
- サーバー: FastAPI + Uvicorn
- フロント: React + TypeScript + Tailwind CSS + Leaflet（地図表示）
- Python パッケージ管理: uv
- テスト: pytest + vitest

## ディレクトリ所有権（並列開発用）

| ディレクトリ | 担当 | 権限 |
|------------|------|------|
| backend/app/schemas.py | api-server | 定義・編集（型定義の正） |
| backend/ | api-server | 専有 |
| planner/ | route-planner | 専有 |
| client/ | frontend | 専有 |
| eval/ | evaluator | 専有 |

## 重要ルール
- 各担当は自分のディレクトリのみ編集すること
- schemas.py は api-server 担当が最初に定義する
- 他チームは schemas.py を読み取り専用でインポート
- 外部APIキーは環境変数で管理（.env）
- OpenMeteo APIはキー不要なので優先的に使う

## 依存関係
1. backend/app/schemas.py → api-server が最初に定義
2. planner/ → schemas.py をインポート
3. backend/app/routers/ → planner/ のエクスポートに依存
4. client/ → backend の API仕様に依存
5. eval/ → backend と planner をインポート

## API設計

### POST /api/plan
ルート生成リクエスト → LLMが分析してルート提案
- Request:
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
- Response: SSE stream
  - event: route_data → ルート座標・標高データ
  - event: weather → 天気予報データ
  - event: token → LLMの分析テキスト（ストリーミング）
  - event: done

### GET /api/weather?lat=...&lng=...&date=...
指定地点の天気予報取得
- Response: { data: WeatherForecast }

### GET /api/elevation?points=...
ルート上の標高プロファイル取得
- Response: { data: ElevationProfile }

### GET /api/history
過去のルート提案履歴
- Response: { data: list[RoutePlan] }

## データモデル（schemas.py に定義）

```python
class Location(BaseModel):
    lat: float
    lng: float
    name: str | None = None

class RoutePreferences(BaseModel):
    difficulty: str  # "easy" | "moderate" | "hard"
    avoid_traffic: bool = True
    prefer_scenic: bool = True
    max_distance_km: float | None = None
    max_elevation_gain_m: float | None = None

class PlanRequest(BaseModel):
    origin: Location
    destination: Location
    preferences: RoutePreferences
    departure_time: datetime

class RouteSegment(BaseModel):
    coordinates: list[tuple[float, float]]  # (lat, lng)
    distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float
    estimated_duration_min: int
    surface_type: str  # "paved" | "gravel" | "dirt"

class WeatherForecast(BaseModel):
    time: datetime
    temperature: float
    wind_speed: float
    wind_direction: float
        precipitation_probability: float
    weather_code: int
    description: str

class RoutePlan(BaseModel):
    id: str
    segments: list[RouteSegment]
    total_distance_km: float
    total_elevation_gain_m: float
    total_duration_min: int
    weather_forecasts: list[WeatherForecast]
    llm_analysis: str           # LLMによるルート分析・アドバイス
    warnings: list[str]         # 注意事項（強風、雨予報など）
    recommended_gear: list[str] # 推奨装備
    created_at: datetime
```

## コーディング規約
- Python: ruff フォーマット、mypy strict mode、型ヒント必須
- docstring は Google style
- 非同期処理は async/await で統一
- エラーは FastAPI の HTTPException で統一
- 外部API呼び出しは httpx の AsyncClient を使用

## コマンド
```bash
make setup     # 初回セットアップ
make dev       # バックエンド + フロント同時起動
make test      # 全テスト実行
make eval      # ルート品質評価
make typecheck # mypy
```
