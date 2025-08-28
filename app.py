import os
import json
import uuid
import asyncio
import random
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# OpenAI API設定
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

try:
    from openai import OpenAI
    import shogi
    import shogi.CSA
except ImportError:
    raise SystemExit(
        "必要なライブラリをインストールしてください: pip install openai python-shogi"
    )

# OpenAIクライアントの初期化
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print(
            "警告: OpenAI APIキーが設定されていません。.envファイルにAPIキーを設定してください。"
        )
        print("サンプルデータモードで動作します。")
        client = None
    else:
        client = OpenAI(api_key=api_key)
        print("OpenAI クライアントが正常に初期化されました")
        # 簡単な接続テスト
        try:
            # モデル一覧を取得してAPIキーの有効性を確認
            models = client.models.list()
            print("OpenAI API接続確認: 成功")
        except Exception as test_error:
            print(f"OpenAI API接続テスト失敗: {test_error}")
            print("APIキーが無効か、ネットワークエラーの可能性があります。")
            client = None
except Exception as e:
    print(f"OpenAI client initialization failed: {e}")
    print("AIコメント機能は無効になりますが、基本機能は動作します")
    client = None

app = Flask(__name__)

# グローバル変数でゲームデータを保存
generated_games = {}

# バージョン情報
APP_VERSION = "1.0.0"
print(f"AIの将棋トレーニング v{APP_VERSION} 起動中...")
print(f"OpenAI API設定: {'有効' if client else '無効（サンプルデータモード）'}")

# サンプル棋譜データ（30手の完全な対局）
SAMPLE_GAME_DATA = {
    "gameId": f"20250827-{uuid.uuid4().hex[:8]}",
    "sente": "宗太郎君 AI",
    "gote": "四五六君 AI",
    "moves": [
        {
            "moveNumber": 1,
            "moveUsi": "7g7f",
            "moveNotation": "７六歩",
            "commentary": "先手、角道を開ける定跡の一手。序盤の基本中の基本です。",
        },
        {
            "moveNumber": 2,
            "moveUsi": "3c3d",
            "moveNotation": "３四歩",
            "commentary": "後手も角道を開けて対抗。お互いに駒の利きを良くする布石段階です。",
        },
        {
            "moveNumber": 3,
            "moveUsi": "2g2f",
            "moveNotation": "２六歩",
            "commentary": "飛車先の歩を突く。飛車の活用を図る積極的な手です。",
        },
        {
            "moveNumber": 4,
            "moveUsi": "4c4d",
            "moveNotation": "４四歩",
            "commentary": "角の利きを止めつつ、中央の歩を伸ばす堅実な指し手。",
        },
        {
            "moveNumber": 5,
            "moveUsi": "2f2e",
            "moveNotation": "２五歩",
            "commentary": "さらに飛車先を伸ばし、攻撃の意思を明確にしています。",
        },
        {
            "moveNumber": 6,
            "moveUsi": "8c8d",
            "moveNotation": "８四歩",
            "commentary": "後手も飛車先の歩を突いて対抗。バランスの取れた指し回しです。",
        },
        {
            "moveNumber": 7,
            "moveUsi": "6i7h",
            "moveNotation": "７八玉",
            "commentary": "玉の安全確保を図る。攻めと守りのバランスを重視した手です。",
        },
        {
            "moveNumber": 8,
            "moveUsi": "8d8e",
            "moveNotation": "８五歩",
            "commentary": "飛車先を突破し、先手の飛車にプレッシャーをかけます。",
        },
        {
            "moveNumber": 9,
            "moveUsi": "2h2i",
            "moveNotation": "２九飛",
            "commentary": "飛車を下がって安全を確保。冷静な判断です。",
        },
        {
            "moveNumber": 10,
            "moveUsi": "4a3b",
            "moveNotation": "３二金",
            "commentary": "玉の守りを固める金上がり。堅実な駒組みを続けます。",
        },
        {
            "moveNumber": 11,
            "moveUsi": "5i6h",
            "moveNotation": "６八銀",
            "commentary": "銀を上がって玉の守りを強化。美濃囲いを目指します。",
        },
        {
            "moveNumber": 12,
            "moveUsi": "7a6b",
            "moveNotation": "６二銀",
            "commentary": "後手も銀を上がって玉の守りを固めます。",
        },
        {
            "moveNumber": 13,
            "moveUsi": "6h7g",
            "moveNotation": "７七銀",
            "commentary": "銀をさらに前進。角道の守りも兼ねた好手です。",
        },
        {
            "moveNumber": 14,
            "moveUsi": "5a4b",
            "moveNotation": "４二玉",
            "commentary": "玉を安全地帯に移動。金銀の守りを固めていきます。",
        },
        {
            "moveNumber": 15,
            "moveUsi": "8h7i",
            "moveNotation": "７九角",
            "commentary": "角を引いて守りを固めつつ、後の反撃に備えます。",
        },
        {
            "moveNumber": 16,
            "moveUsi": "6c6d",
            "moveNotation": "６四歩",
            "commentary": "中央の歩を突いて陣形を整備。バランスの良い指し手です。",
        },
        {
            "moveNumber": 17,
            "moveUsi": "7h8h",
            "moveNotation": "８八玉",
            "commentary": "玉をさらに安全な位置に移動。美濃囲いの完成を目指します。",
        },
        {
            "moveNumber": 18,
            "moveUsi": "6b6c",
            "moveNotation": "６三銀",
            "commentary": "銀を中央に展開。攻守にバランスの取れた配置です。",
        },
        {
            "moveNumber": 19,
            "moveUsi": "9g9f",
            "moveNotation": "９六歩",
            "commentary": "端歩を突いて香車の活用を図ります。",
        },
        {
            "moveNumber": 20,
            "moveUsi": "1c1d",
            "moveNotation": "１四歩",
            "commentary": "後手も端歩で対抗。香車の利きを通します。",
        },
        {
            "moveNumber": 21,
            "moveUsi": "1g1f",
            "moveNotation": "１六歩",
            "commentary": "端攻めの準備を進める。香車の活用を見据えています。",
        },
        {
            "moveNumber": 22,
            "moveUsi": "7c7d",
            "moveNotation": "７四歩",
            "commentary": "歩を突いて陣形を整備。駒組みが着実に進んでいます。",
        },
        {
            "moveNumber": 23,
            "moveUsi": "3i4h",
            "moveNotation": "４八金",
            "commentary": "金を上がって玉の守りを一層強化します。",
        },
        {
            "moveNumber": 24,
            "moveUsi": "5c5d",
            "moveNotation": "５四歩",
            "commentary": "中央で主導権を握ろうとする積極的な歩突き。",
        },
        {
            "moveNumber": 25,
            "moveUsi": "5g5f",
            "moveNotation": "５六歩",
            "commentary": "中央で歩をぶつけて戦いを誘発。局面が動き始めます。",
        },
        {
            "moveNumber": 26,
            "moveUsi": "6c5d",
            "moveNotation": "５四銀",
            "commentary": "銀で歩を取り、中央に拠点を築く。攻撃の足がかりです。",
        },
        {
            "moveNumber": 27,
            "moveUsi": "5f5e",
            "moveNotation": "５五歩",
            "commentary": "歩を突いて銀にプレッシャー。反撃開始です。",
        },
        {
            "moveNumber": 28,
            "moveUsi": "5d4c",
            "moveNotation": "４三銀",
            "commentary": "銀を引いて安定化を図る。守備重視の判断です。",
        },
        {
            "moveNumber": 29,
            "moveUsi": "7g6f",
            "moveNotation": "６六銀",
            "commentary": "銀を前進させて攻撃の体勢を整える。決戦が近づいています。",
        },
        {
            "moveNumber": 30,
            "moveUsi": "4b5b",
            "moveNotation": "５二玉",
            "commentary": "玉をより安全な位置に移動。後手の受けが巧妙です。この局面で先手有利となり、対局終了。",
        },
    ],
    "result": "",
    "winReason": "",
}
