# GCP Cloud Run デプロイ手順

このガイドでは、Cycling Route PlannerをGoogle Cloud Platform (GCP) のCloud Runにデプロイする手順を説明します。

## 前提条件

- GCPアカウント
- Google Cloud SDK (`gcloud`) のインストール
- プロジェクトの作成済み

## 初回セットアップ

### 1. gcloud CLIのインストールと認証

```bash
# gcloud CLIをインストール（未インストールの場合）
# https://cloud.google.com/sdk/docs/install

# 認証
gcloud auth login

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# Cloud Run APIを有効化
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Secret Managerにシークレットを登録

```bash
# ANTHROPIC_API_KEYを登録
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key --data-file=-

# ORS_API_KEYを登録
echo -n "YOUR_ORS_API_KEY" | gcloud secrets create ors-api-key --data-file=-
```

## バックエンドのデプロイ

### 1. Dockerイメージをビルドしてデプロイ

```bash
# プロジェクトルートから実行
cd /path/to/cycling-route-planner

# Cloud Runにデプロイ（自動ビルド）
gcloud run deploy cycling-backend \
  --source . \
  --dockerfile backend/Dockerfile \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-secrets=ANTHROPIC_API_KEY=anthropic-api-key:latest,ORS_API_KEY=ors-api-key:latest \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --port 8080

# デプロイ後、URLが表示されます
# 例: https://cycling-backend-xxxxx-an.a.run.app
```

### 2. バックエンドURLを記録

デプロイ後に表示されるURLを記録してください（フロントエンド設定で使用します）。

```bash
# URLを取得
gcloud run services describe cycling-backend \
  --region asia-northeast1 \
  --format 'value(status.url)'
```

## フロントエンドのデプロイ

### 1. 環境変数ファイルを作成

```bash
# client/.env.production を作成
cd client
cat > .env.production << EOF
VITE_API_BASE_URL=https://cycling-backend-xxxxx-an.a.run.app
EOF
```

### 2. フロントエンドをデプロイ

```bash
# プロジェクトルートに戻る
cd ..

# Cloud Runにデプロイ
gcloud run deploy cycling-frontend \
  --source . \
  --dockerfile client/Dockerfile \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --port 8080

# デプロイ後、URLが表示されます
# 例: https://cycling-frontend-xxxxx-an.a.run.app
```

### 3. バックエンドのCORS設定を更新

フロントエンドのURLをバックエンドに設定します。

```bash
# フロントエンドURLを環境変数として設定
gcloud run services update cycling-backend \
  --region asia-northeast1 \
  --set-env-vars=FRONTEND_URL=https://cycling-frontend-xxxxx-an.a.run.app
```

## 動作確認

1. フロントエンドURL（`https://cycling-frontend-xxxxx-an.a.run.app`）にアクセス
2. 出発地・目的地を設定してルート生成をテスト
3. 標高プロファイル、LLM分析が正しく表示されることを確認

## 更新デプロイ

コードを変更した場合、以下のコマンドで再デプロイできます。

```bash
# バックエンド更新
gcloud run deploy cycling-backend \
  --source . \
  --dockerfile backend/Dockerfile \
  --region asia-northeast1

# フロントエンド更新
gcloud run deploy cycling-frontend \
  --source . \
  --dockerfile client/Dockerfile \
  --region asia-northeast1
```

## コスト管理

Cloud Runは従量課金です。以下の方法でコストを抑えられます：

```bash
# 最小インスタンス数を0に設定（デフォルト）
gcloud run services update cycling-backend \
  --region asia-northeast1 \
  --min-instances 0

# 最大インスタンス数を制限
gcloud run services update cycling-backend \
  --region asia-northeast1 \
  --max-instances 10
```

## トラブルシューティング

### ログの確認

```bash
# バックエンドログ
gcloud run logs read cycling-backend --region asia-northeast1 --limit 50

# フロントエンドログ
gcloud run logs read cycling-frontend --region asia-northeast1 --limit 50
```

### シークレットの確認

```bash
# 登録されているシークレットを確認
gcloud secrets list

# シークレットの値を確認（テスト用）
gcloud secrets versions access latest --secret=anthropic-api-key
```

### デバッグモード

```bash
# バックエンドをデバッグモードで起動
gcloud run services update cycling-backend \
  --region asia-northeast1 \
  --set-env-vars=LOG_LEVEL=debug
```

## カスタムドメインの設定（オプション）

独自ドメインを使用する場合：

```bash
# ドメインマッピングを作成
gcloud run domain-mappings create \
  --service cycling-frontend \
  --domain your-domain.com \
  --region asia-northeast1
```

## セキュリティ強化（オプション）

### 認証の追加

```bash
# 認証を有効化（Firebase Authenticationなどと連携）
gcloud run services update cycling-frontend \
  --region asia-northeast1 \
  --no-allow-unauthenticated
```

## サービスの削除

不要になった場合：

```bash
# サービスを削除
gcloud run services delete cycling-backend --region asia-northeast1
gcloud run services delete cycling-frontend --region asia-northeast1

# シークレットを削除
gcloud secrets delete anthropic-api-key
gcloud secrets delete ors-api-key
```

## 参考リンク

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Run 料金](https://cloud.google.com/run/pricing)
