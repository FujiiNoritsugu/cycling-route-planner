# Cycling Route Planner Module

サイクリングルート生成パイプラインの実装。地図・天気・標高データを統合してClaudeに渡すコンテキストを構築します。

## ディレクトリ構成

```
planner/
├── __init__.py              # パッケージエクスポート
├── schemas.py               # データモデル定義（backend/app/schemas.py から移行予定）
├── route_generator.py       # OpenRouteService API統合
├── weather_client.py        # OpenMeteo API統合（APIキー不要）
├── elevation.py             # 標高プロファイル取得・計算
├── analyzer.py              # データ統合＆Claude用コンテキスト構築
├── risk_assessor.py         # リスクレベル判定・装備推奨
└── tests/                   # テストスイート
    ├── conftest.py          # pytest fixtures
    ├── test_route_generator.py
    ├── test_weather_client.py
    ├── test_elevation.py
    ├── test_analyzer.py
    └── test_risk_assessor.py
```

## 公開インターフェース

### RouteGenerator
OpenRouteService APIでルート生成

```python
from planner import RouteGenerator

generator = RouteGenerator(api_key="your_ors_key")
segments = await generator.generate_route(origin, destination, preferences)
```

**主要メソッド:**
- `async generate_route(origin, destination, preferences, profile="cycling-regular")` → `list[RouteSegment]`

### WeatherClient
OpenMeteo APIで天気予報取得（APIキー不要）

```python
from planner import WeatherClient

client = WeatherClient()
forecasts = await client.get_forecast(location, start_time, hours=24)
route_forecasts = await client.get_route_forecast(locations, start_time, duration_hours)
```

**主要メソッド:**
- `async get_forecast(location, start_time, hours=24)` → `list[WeatherForecast]`
- `async get_route_forecast(locations, start_time, duration_hours)` → `list[WeatherForecast]`

### ElevationService
標高プロファイル取得・計算

```python
from planner import ElevationService

service = ElevationService()
elevations = await service.get_elevation_profile(coordinates)
gain, loss = await service.calculate_elevation_stats(elevations)
```

**主要メソッド:**
- `async get_elevation_profile(coordinates)` → `list[float]`
- `async calculate_elevation_stats(elevations)` → `tuple[float, float]`

### RouteAnalyzer
全データを統合してClaude用コンテキスト構築

```python
from planner import RouteAnalyzer

analyzer = RouteAnalyzer()
context = analyzer.build_context(
    origin, destination, segments, weather_forecasts,
    elevation_profile, preferences, warnings, gear
)
stats = analyzer.summarize_route_stats(segments)
```

**主要メソッド:**
- `build_context(...)` → `str` - Claude用プロンプトコンテキスト
- `summarize_route_stats(segments)` → `dict` - ルート統計情報

### RiskAssessor
天気・標高・距離からリスク評価と装備推奨

```python
from planner import RiskAssessor

assessor = RiskAssessor()
warnings, gear = assessor.assess_route(segments, weather_forecasts, preferences)
risk_score = assessor.calculate_risk_score(segments, weather_forecasts)
```

**主要メソッド:**
- `assess_route(segments, weather_forecasts, preferences)` → `tuple[list[str], list[str]]`
- `calculate_risk_score(segments, weather_forecasts)` → `float` (0-100)

## データモデル

主要なデータモデルは `planner.schemas` で定義されています：

- `Location` - 地理的位置（緯度、経度、名前）
- `RoutePreferences` - ユーザーの好み設定
- `RouteSegment` - ルートの一区間
- `WeatherForecast` - 天気予報データ
- `RoutePlan` - 完全なルート計画（分析含む）

## 実装の特徴

### 外部API統合
- **OpenRouteService**: ルート生成、標高データ（要APIキー）
- **OpenMeteo**: 天気予報、標高データ（APIキー不要）
- すべての外部API呼び出しは `httpx.AsyncClient` で実装
- API障害時のフォールバック処理を実装

### リスク評価ロジック
- **風速** > 10m/s → 警告
- **降水確率** > 50% → 警告
- **獲得標高** > 2000m → ハードモード警告
- **気温** < 5℃ or > 35℃ → 警告
- 条件に応じて推奨装備を自動生成

### Claude用コンテキスト構築
`RouteAnalyzer.build_context()` は以下の情報を含む構造化テキストを生成：
1. ルート概要（距離、標高、所要時間）
2. ユーザー設定
3. 標高プロファイル分析
4. 天気予報サマリー
5. セグメント詳細
6. 警告・推奨装備
7. 分析リクエストプロンプト

## テスト

```bash
# 全テスト実行
pytest planner/tests/

# 特定モジュールのテスト
pytest planner/tests/test_route_generator.py -v

# カバレッジ付き
pytest planner/tests/ --cov=planner --cov-report=html
```

**テスト結果**: 66 tests passed (100%)

## 環境変数

`.env` ファイルに以下を設定：

```env
# OpenRouteService API（ルート生成に必要）
ORS_API_KEY=your_api_key_here

# OpenMeteo API はキー不要
```

## 使用例

```python
from planner import (
    RouteGenerator, WeatherClient, ElevationService,
    RouteAnalyzer, RiskAssessor
)
from planner.schemas import Location, RoutePreferences
from datetime import datetime

# 1. ルート生成
generator = RouteGenerator()
origin = Location(lat=34.573, lng=135.483, name="堺市")
destination = Location(lat=34.396, lng=135.757, name="吉野山")
preferences = RoutePreferences(
    difficulty="moderate",
    avoid_traffic=True,
    prefer_scenic=True,
    max_distance_km=100.0,
    max_elevation_gain_m=1500.0,
)

segments = await generator.generate_route(origin, destination, preferences)

# 2. 天気予報取得
weather_client = WeatherClient()
start_time = datetime(2025, 3, 15, 7, 0)
coordinates = [seg.coordinates for seg in segments]
locations = [Location(lat=c[0], lng=c[1]) for seg in segments for c in seg.coordinates[::10]]
forecasts = await weather_client.get_route_forecast(locations, start_time, duration_hours=5)

# 3. 標高プロファイル
elevation_service = ElevationService()
all_coords = [coord for seg in segments for coord in seg.coordinates]
elevations = await elevation_service.get_elevation_profile(all_coords)

# 4. リスク評価
assessor = RiskAssessor()
warnings, gear = assessor.assess_route(segments, forecasts, preferences)
risk_score = assessor.calculate_risk_score(segments, forecasts)

# 5. Claude用コンテキスト構築
analyzer = RouteAnalyzer()
context = analyzer.build_context(
    origin, destination, segments, forecasts,
    elevations, preferences, warnings, gear
)

# 6. Claudeに渡して分析
# (backend チームが実装)
```

## 今後の改善予定

- [ ] backend/app/schemas.py からの型定義インポート
- [ ] OpenRouteService Elevation API の完全統合
- [ ] ルートキャッシング機能
- [ ] より詳細な路面タイプ推定
- [ ] 交通量データの統合
- [ ] ルート最適化アルゴリズム改善

## 依存パッケージ

- `httpx` >= 0.27.0 - 非同期HTTP通信
- `pydantic` >= 2.9.0 - データ検証・モデル
- `python-dotenv` >= 1.0.0 - 環境変数管理
- `pytest` >= 8.3.0 - テストフレームワーク
- `pytest-asyncio` >= 0.24.0 - 非同期テストサポート
