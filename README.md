# 将棋AI対局・解説アプリケーション

AI同士の将棋対局をリアルタイムで解説付きで観戦できるWebアプリケーションです。

## 機能

- **AI対局機能**: 実際のAI対局生成
- **AI解説機能**: OpenAI GPT-4o-miniによる一手一手の詳細解説
- **棋譜ビューア機能**: インタラクティブな棋譜閲覧
- **盤面表示**: リアルタイムな盤面と持ち駒の表示
- **自動フォールバック**: API制限時はサンプルデータで動作継続

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`を `.env`にコピーして、OpenAI APIキーを設定してください：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```
OPENAI_API_KEY=sk-your_actual_openai_api_key_here
```

### 3. アプリケーションの起動

```bash
python app.py
```

アプリケーションは `http://localhost:8080` で起動します。

## 使用方法

1. ブラウザで `http://localhost:8080` にアクセス
2. 「対局開始」ボタンをクリック
3. AI対局の生成を待つ（20手で30-60秒程度）
   - OpenAI APIキーが設定されている場合：リアルタイムAI対局
4. 棋譜ビューアで対局を閲覧
   - 棋譜リストをクリックして好きな手数に移動
   - 矢印キーでナビゲーション
   - AI解説を読みながら対局を学習

## AI機能の仕組み

### AI対局生成

1. **手生成**: OpenAI GPT-4o-miniが現在の局面から次の最適手を選択
2. **解説生成**: 各手について戦術的な解説をAIが自動生成
3. **対局進行**: 最大手まで自動で対局を進行

### パフォーマンス

- 初回生成時間: 30-60秒程度（20手分の対局）
- API呼び出し: 1手あたり約1-2秒

## プロジェクト構造

```
Shogi/
├── app.py                 # メインのFlaskアプリケーション
├── requirements.txt       # 必要なライブラリ
├── .env.example          # 環境変数のサンプル
├── templates/            # HTMLテンプレート
│   ├── index.html        # メインページ
│   └── viewer.html       # 棋譜ビューア
└── static/              # 静的ファイル
    ├── css/
    │   └── style.css     # スタイルシート
    └── js/
        ├── main.js       # メインページのJavaScript
        └── viewer.js     # ビューアのJavaScript
```

## 開発状況

- ✅ 基本的なWebアプリケーション構造
- ✅ **実際のAI対局生成機能**（OpenAI GPT-4o-miniを使用）
- ✅ **リアルタイムAI解説機能**
- ✅ インタラクティブな盤面表示
- ✅ 持ち駒表示
- ✅ 棋譜ダウンロード機能
- ✅ エラーハンドリングとフォールバック

## 技術スタック

- **バックエンド**: Flask
- **将棋ロジック**: python-shogi
- **AI**: OpenAI API
- **フロントエンド**: HTML, CSS, JavaScript (素のJS)
