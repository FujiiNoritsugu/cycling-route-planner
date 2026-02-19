# Cycling Route Planner - Frontend

React + TypeScript + Leaflet による サイクリングルートプランナーのフロントエンド実装。

## 技術スタック

- **React 18** - UI フレームワーク
- **TypeScript** - 型安全性
- **Vite** - ビルドツール
- **Tailwind CSS** - スタイリング
- **React Leaflet** - 地図表示
- **Recharts** - グラフ描画
- **React Markdown** - Markdown レンダリング

## ディレクトリ構成

```
client/
├── src/
│   ├── types.ts                # TypeScript 型定義
│   ├── components/
│   │   ├── RouteMap.tsx        # Leaflet 地図コンポーネント
│   │   ├── PlanForm.tsx        # ルート設定フォーム
│   │   ├── WeatherPanel.tsx    # 天気予報表示
│   │   ├── AnalysisPanel.tsx   # AI分析表示
│   │   └── ElevationChart.tsx  # 標高グラフ
│   ├── hooks/
│   │   └── usePlan.ts          # ルート生成 SSE フック
│   ├── App.tsx                 # メインアプリケーション
│   ├── main.tsx                # エントリーポイント
│   └── index.css               # グローバルスタイル
├── vite.config.ts              # Vite 設定 (API プロキシ含む)
├── tailwind.config.js          # Tailwind CSS 設定
└── package.json
```

## 実装内容

### 1. 型定義 (`types.ts`)
backend/app/schemas.py に対応する TypeScript 型定義:
- `Location` - 位置情報
- `RoutePreferences` - ルート設定
- `PlanRequest` - リクエスト
- `RouteSegment` - ルート区間
- `WeatherForecast` - 天気予報
- `RoutePlan` - ルートプラン全体
- `SSEEvent` - SSE イベント型

### 2. コンポーネント

#### RouteMap.tsx
- react-leaflet で地図表示
- デフォルト中心: 大阪周辺 [34.6, 135.5]
- ルートライン表示（標高による色分け）
- 出発地/到着地マーカー
- 地図クリックで位置設定

#### PlanForm.tsx
- 出発地/目的地入力フォーム
- 難易度選択 (easy/moderate/hard)
- 好み設定 (交通量、景色、距離、標高)
- 出発時刻選択
- ルート生成ボタン

#### WeatherPanel.tsx
- 時間帯別天気予報タイムライン
- 天気アイコン、気温、風速、降水確率
- 警告表示（赤字強調）

#### AnalysisPanel.tsx
- LLM 分析テキストのストリーミング表示
- Markdown レンダリング
- タイプライター効果
- 推奨装備リスト

#### ElevationChart.tsx
- recharts で標高プロファイルグラフ
- 距離-標高のエリアチャート
- 勾配情報の表示
- 統計情報（総距離、最高標高、獲得標高）

### 3. カスタムフック

#### usePlan.ts
- fetch + ReadableStream で SSE 受信
- POST /api/plan にリクエスト送信
- イベントタイプ別処理:
  - `route_data` → ルートデータ更新
  - `weather` → 天気データ更新
  - `token` → LLM テキスト追加
  - `done` → ローディング終了
  - `error` → エラー表示

### 4. レイアウト (App.tsx)
- 3カラムレスポンシブレイアウト:
  - 左: PlanForm
  - 中央: RouteMap
  - 右: WeatherPanel + AnalysisPanel + ElevationChart
- クリックモード切り替え機能
- リセットボタン

## API プロキシ設定

vite.config.ts で `/api` を `http://localhost:8000` にプロキシ:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## コマンド

```bash
# 依存パッケージインストール
npm install

# 開発サーバー起動 (localhost:5173)
npm run dev

# ビルド
npm run build

# プレビュー
npm run preview

# テスト
npm test

# Lint
npm run lint
```

## ビルド結果

ビルド成功:
- `dist/index.html` - 0.47 kB
- `dist/assets/index-*.css` - 47.50 kB
- `dist/assets/index-*.js` - 860.33 kB

## レスポンシブデザイン

- モバイル: 1カラム縦並び
- タブレット: 2カラム
- デスクトップ: 3カラム (lg:grid-cols-12)

## 特徴

- TypeScript による型安全性
- SSE によるリアルタイムストリーミング
- Leaflet による高機能な地図表示
- Recharts による美しいグラフ
- Tailwind CSS によるレスポンシブデザイン
- React Markdown による AI 分析のリッチな表示

## 次のステップ

バックエンド API 実装後:
1. `npm run dev` で開発サーバー起動
2. ブラウザで `http://localhost:5173` にアクセス
3. 地図をクリックして出発地/目的地を設定
4. ルート生成ボタンをクリック
5. SSE ストリームで結果を受信・表示
