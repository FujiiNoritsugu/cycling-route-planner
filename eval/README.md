# Evaluation System

サイクリングルート提案の品質評価とパフォーマンス計測を行うツール群。

## ディレクトリ構成

```
eval/
├── test_routes.json         # テスト用ルートリクエスト5件
├── evaluate.py              # LLM-as-Judge で品質採点
├── bench_api.py             # API パフォーマンス計測
├── requirements.txt         # Python 依存パッケージ
└── results/                 # 評価結果の保存先
    ├── evaluation_results.json
    └── benchmark_results.json
```

## セットアップ

```bash
# 依存パッケージのインストール
pip install -r eval/requirements.txt

# または uv を使用
uv pip install -r eval/requirements.txt

# 環境変数の設定
export ANTHROPIC_API_KEY=your_api_key_here
```

## テストケース

`test_routes.json` に以下の5つのテストケースを定義:

1. **堺市上野芝 → 吉野山** (ロングライド、山岳)
2. **堺 → 六甲山** (ヒルクライム)
3. **大和川サイクリングロード往復** (初心者向け平坦)
4. **堺 → 暗峠** (激坂チャレンジ)
5. **大阪 → 琵琶湖** (超ロングライド)

## 品質評価 (evaluate.py)

LLM-as-Judge パターンでルート提案品質を評価します。

### 評価軸

1. **安全性** (1-10点): 交通量、路面状態、リスク評価の適切性
2. **天気対応** (1-10点): 天気情報の活用、警告の適切性
3. **実用性** (1-10点): 距離・時間の妥当性、補給ポイント提案
4. **ユーザー満足度** (1-10点): 好みへの対応、アドバイスの質
5. **総合評価** (1-10点): 上記を踏まえた総合的な品質

### 実行方法

```bash
# 評価実行
python eval/evaluate.py

# 結果は eval/results/evaluation_results.json に保存されます
```

### 動作モード

- **Backend/Planner が利用可能な場合**: 実際のルート提案を評価
- **Backend/Planner が未実装の場合**: モックデータで評価システムの動作確認

### 出力例

```
=== Cycling Route Quality Evaluation ===

Loaded 5 test cases

[1/5] Evaluating: 堺市上野芝 → 吉野山（ロングライド、山岳）
  - Safety: 8/10
  - Weather: 7/10
  - Practicality: 9/10
  - User Satisfaction: 8/10
  - Overall: 8/10

...

=== Summary ===
Test Case                                          Safety   Weather  Practical  User Sat   Overall
----------------------------------------------------------------------------------------------------
堺市上野芝 → 吉野山（ロングライド、山岳）              8        7        9          8          8
...
```

## パフォーマンス計測 (bench_api.py)

API 応答時間を計測し、パフォーマンス指標を取得します。

### 計測項目

- **TTFB** (Time To First Byte): ストリーミング開始までの時間
- **Total Time**: 完了までの総時間
- **Success Rate**: 成功率
- **Percentiles**: P50 / P95 / P99 レイテンシ

### 実行方法

```bash
# デフォルト設定 (10回実行)
python eval/bench_api.py

# 実行回数を指定
python eval/bench_api.py --iterations 20

# API URLを指定
python eval/bench_api.py --api-url http://localhost:8000/api/plan

# 結果は eval/results/benchmark_results.json に保存されます
```

### 前提条件

- バックエンドサーバーが起動していること (`make dev`)
- API エンドポイントが利用可能であること

### 出力例

```
=== Cycling Route API Performance Benchmark ===

Target API: http://localhost:8000/api/plan
Iterations per test case: 10

[1/5] Benchmarking: 堺市上野芝 → 吉野山（ロングライド、山岳）
  Running 10 iterations...
    [1/10] TTFB: 250ms, Total: 3000ms
    [2/10] TTFB: 240ms, Total: 2950ms
    ...
  ✓ Success rate: 100.0%
  ✓ TTFB p50/p95/p99: 245ms / 280ms / 300ms
  ✓ Total p50/p95/p99: 2980ms / 3200ms / 3500ms

=== Summary Table ===
Test Case                                          Success%   TTFB p50     TTFB p95     Total p50    Total p95
--------------------------------------------------------------------------------------------------------------------
堺市上野芝 → 吉野山（ロングライド、山岳）              100.0%     245ms        280ms        2980ms       3200ms
...
```

## 結果ファイル

### evaluation_results.json

```json
{
  "evaluated_at": "2025-03-15T10:30:00",
  "total_cases": 5,
  "results": [
    {
      "test_case_name": "堺市上野芝 → 吉野山（ロングライド、山岳）",
      "evaluation": {
        "safety": {
          "score": 8,
          "reason": "交通量の多い道路を適切に回避..."
        },
        "weather_integration": {
          "score": 7,
          "reason": "天気情報を活用し、適切な警告..."
        },
        ...
      },
      "evaluated_at": "2025-03-15T10:30:00"
    }
  ]
}
```

### benchmark_results.json

```json
{
  "benchmarked_at": "2025-03-15T10:30:00",
  "api_url": "http://localhost:8000/api/plan",
  "num_iterations": 10,
  "total_cases": 5,
  "results": [
    {
      "test_case": "堺市上野芝 → 吉野山（ロングライド、山岳）",
      "success_rate": 1.0,
      "ttfb_ms": {
        "p50": 245.0,
        "p95": 280.0,
        "p99": 300.0,
        "min": 230.0,
        "max": 310.0,
        "mean": 250.5
      },
      "total_time_ms": {
        "p50": 2980.0,
        "p95": 3200.0,
        "p99": 3500.0,
        "min": 2850.0,
        "max": 3600.0,
        "mean": 3050.2
      }
    }
  ]
}
```

## 開発ガイドライン

### コーディング規約

- Python: ruff フォーマット、mypy strict mode
- 型ヒント必須
- docstring は Google style
- 非同期処理は async/await で統一

### インポート規則

- `backend.app.schemas` から型定義をインポート
- backend と planner は読み取り専用
- eval/ ディレクトリのみ編集可能

### エラーハンドリング

- Backend が利用不可の場合はモックデータで動作
- API エラーは適切にログ出力
- 結果ファイルには error フィールドでエラー記録
