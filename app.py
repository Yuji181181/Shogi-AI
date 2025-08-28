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


class ShogiGame:
    def __init__(self):
        self.board = shogi.Board()
        self.moves = []
        self.commentaries = []

    def board_to_japanese_string(self, board):
        """盤面を日本語の漢字で表示する（色分け用マーカー付き）"""
        try:
            print("テキスト盤面生成を開始")  # デバッグ用
            # 通常のテキスト盤面を生成
            lines = []

            # 各段を処理（枠線なし）
            rank_names = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]

            for rank in range(9):
                line = ""

                for file in range(9):
                    try:
                        # convert_usi_to_japanese関数と同じ座標系を使用
                        # 将棋盤面は9筋から1筋（右から左）なので、fileを逆順で表示
                        # USI座標: to_square = rank * 9 + file (0-80)
                        # 日本語座標: to_file = (to_square % 9) + 1, to_rank = (to_square // 9) + 1
                        display_file = 8 - file  # 9筋から1筋の順番で表示
                        square_index = rank * 9 + display_file
                        piece = board.piece_at(square_index)

                        if piece is None:
                            line += "・"
                        else:
                            # 駒の日本語名を取得
                            piece_name = self.get_piece_japanese_name(piece)
                            # 後手の駒には特殊マーカーを付ける（python-shogiではWHITEが後手）
                            try:
                                is_gote = piece.color == shogi.WHITE
                            except:
                                is_gote = str(piece).isupper()

                            if is_gote:
                                # 後手の駒にマーカーを付ける（後でCSSで置換）
                                line += f"◆{piece_name}◆"
                            else:
                                line += piece_name

                    except Exception as e:
                        print(f"駒処理エラー at rank={rank}, file={file}: {e}")
                        line += "？"

                lines.append(line)

            # テキストとして結合
            result = "\n".join(lines)
            print("テキスト盤面生成成功")  # デバッグ用
            return result

        except Exception as e:
            print(f"Error in board_to_japanese_string: {e}")
            import traceback

            traceback.print_exc()
            # エラーの場合は簡単な文字列置換に戻す
            try:
                board_str = str(board)
                # 先手の駒（スペース付きとスペースなし両方）
                board_str = board_str.replace(" P ", " 歩 ").replace("P", "歩")
                board_str = board_str.replace(" L ", " 香 ").replace("L", "香")
                board_str = board_str.replace(" N ", " 桂 ").replace("N", "桂")
                board_str = board_str.replace(" S ", " 銀 ").replace("S", "銀")
                board_str = board_str.replace(" G ", " 金 ").replace("G", "金")
                board_str = board_str.replace(" B ", " 角 ").replace("B", "角")
                board_str = board_str.replace(" R ", " 飛 ").replace("R", "飛")
                board_str = board_str.replace(" K ", " 玉 ").replace("K", "玉")
                # 後手の駒（スペース付きとスペースなし両方）
                board_str = board_str.replace(" p ", " 歩 ").replace("p", "歩")
                board_str = board_str.replace(" l ", " 香 ").replace("l", "香")
                board_str = board_str.replace(" n ", " 桂 ").replace("n", "桂")
                board_str = board_str.replace(" s ", " 銀 ").replace("s", "銀")
                board_str = board_str.replace(" g ", " 金 ").replace("g", "金")
                board_str = board_str.replace(" b ", " 角 ").replace("b", "角")
                board_str = board_str.replace(" r ", " 飛 ").replace("r", "飛")
                board_str = board_str.replace(" k ", " 玉 ").replace("k", "玉")
                # 空きマス
                board_str = board_str.replace(" . ", " ・ ").replace(".", "・")
                return board_str
            except:
                return f"盤面表示エラー: {e}"

    def get_piece_japanese_name(self, piece):
        """駒の日本語名を取得"""
        try:
            # 基本的な駒の種類定義
            piece_names = {
                shogi.PAWN: "歩",
                shogi.LANCE: "香",
                shogi.KNIGHT: "桂",
                shogi.SILVER: "銀",
                shogi.GOLD: "金",
                shogi.BISHOP: "角",
                shogi.ROOK: "飛",
                shogi.KING: "玉",
            }

            # 成駒の種類定義（python-shogiでは元の駒種+8）
            promoted_piece_names = {
                shogi.PAWN + 8: "と",  # 成歩 = と金
                shogi.LANCE + 8: "成香",
                shogi.KNIGHT + 8: "成桂",
                shogi.SILVER + 8: "成銀",
                shogi.BISHOP + 8: "馬",  # 成角 = 龍馬
                shogi.ROOK + 8: "龍",  # 成飛 = 龍王
            }

            # まず成駒かどうか確認
            if piece.piece_type in promoted_piece_names:
                return promoted_piece_names[piece.piece_type]

            # 普通の駒の場合
            elif piece.piece_type in piece_names:
                return piece_names[piece.piece_type]

            # どちらでもない場合（エラー）
            else:
                print(f"Debug: Unknown piece type: {piece.piece_type}")
                return "？"

        except Exception as e:
            print(f"駒名取得エラー: {e}")
            import traceback

            traceback.print_exc()
            return "？"

    def get_board_state(self, move_number=0):
        """指定した手数での盤面状態を取得"""
        temp_board = shogi.Board()
        for i in range(min(move_number, len(self.moves))):
            temp_board.push_usi(self.moves[i])
        return temp_board

    def get_captured_pieces(self, move_number=0):
        """指定した手数での持ち駒を取得"""
        temp_board = self.get_board_state(move_number)

        sente_pieces = {}
        gote_pieces = {}

        # 先手の持ち駒（python-shogiではBLACKが先手）
        for piece_type in shogi.PIECE_TYPES:
            count = temp_board.pieces_in_hand[shogi.BLACK][piece_type]
            if count > 0:
                piece_name = shogi.PIECE_JAPANESE_SYMBOLS[piece_type]
                sente_pieces[piece_name] = count

        # 後手の持ち駒（python-shogiではWHITEが後手）
        for piece_type in shogi.PIECE_TYPES:
            count = temp_board.pieces_in_hand[shogi.WHITE][piece_type]
            if count > 0:
                piece_name = shogi.PIECE_JAPANESE_SYMBOLS[piece_type]
                gote_pieces[piece_name] = count

        return {"sente": sente_pieces, "gote": gote_pieces}


def convert_usi_to_japanese(move_usi, board):
    """USI記法を日本語表記に簡易変換"""
    try:
        move = shogi.Move.from_usi(move_usi)

        # 移動先の座標を日本語に変換
        to_square = move.to_square
        to_file = (to_square % 9) + 1  # 1筋から9筋（USI座標系を将棋座標系に変換）
        to_rank = (to_square // 9) + 1  # 1段から9段

        # 数字を漢数字に変換
        kansuji = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
        file_str = str(to_file)
        rank_str = kansuji[to_rank]

        # 駒の種類を取得
        if move.from_square is not None:
            # 盤上からの移動
            piece = board.piece_at(move.from_square)
            if piece:
                piece_name = ShogiGame().get_piece_japanese_name(piece)
                return f"{file_str}{rank_str}{piece_name}"
        else:
            # 持ち駒からの打ち
            piece_type = move.drop_piece_type
            if piece_type:
                piece_names = {
                    shogi.PAWN: "歩",
                    shogi.LANCE: "香",
                    shogi.KNIGHT: "桂",
                    shogi.SILVER: "銀",
                    shogi.GOLD: "金",
                    shogi.BISHOP: "角",
                    shogi.ROOK: "飛",
                }
                piece_name = piece_names.get(piece_type, "？")
                return f"{file_str}{rank_str}{piece_name}打"

        return f"{file_str}{rank_str}"

    except Exception as e:
        print(f"日本語変換エラー: {e}")
        return move_usi  # エラー時はUSI記法をそのまま返す


async def generate_ai_commentary(board_state, move_usi, move_number, player):
    """指定された手に対するAI解説を生成"""
    if not client:
        return f"{move_number}手目の手です。詳細な解説を表示するにはOpenAI APIキーを設定してください。"

    try:
        # 現在の盤面情報
        board = shogi.Board()
        for i in range(move_number - 1):
            if i < len(SAMPLE_GAME_DATA["moves"]):
                board.push_usi(SAMPLE_GAME_DATA["moves"][i]["moveUsi"])

        # 手の詳細情報を取得
        move = shogi.Move.from_usi(move_usi)
        piece = board.piece_at(move.from_square) if move.from_square else None

        # 手の日本語表記を生成
        move_japanese = convert_usi_to_japanese(move_usi, board)

        # プロンプトを作成
        prompt = f"""
あなたは将棋のプロ解説者です。以下の手について、初心者にもわかりやすい解説をしてください。

手数: {move_number}手目
手番: {player}
指し手(USI): {move_usi}
指し手(日本語): {move_japanese}
駒: {piece.piece_type if piece else '不明'}

以下の点を含めて100文字程度で解説してください：
1. この手の狙いや意図
2. 局面への影響
3. 将棋の基本的なセオリーとの関連

解説は敬語を使わず、親しみやすい口調でお願いします。
駒の位置は「{move_japanese}」のように日本語で表記してください。
将棋の座標系では、1筋から9筋（左から右）、1段から9段（上から下）で表現されます。
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたは将棋の解説者です。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"AI解説生成エラー: {e}")
        return f"{move_number}手目の手です。AI解説の生成中にエラーが発生しました。"


async def generate_ai_move(board, move_number, player_type):
    """AI（GPT）による次の手を生成"""
    if not client:
        # APIキーがない場合は定跡的な手を返す
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None

    try:
        # 現在の盤面状況を文字列で説明
        legal_moves = list(board.legal_moves)
        legal_moves_usi = [move.usi() for move in legal_moves[:10]]  # 最初の10手のみ

        prompt = f"""
あなたは{player_type}の将棋AIです。現在{move_number}手目を指す番です。

以下の合法手の中から最適な手を1つ選んでください：
{', '.join(legal_moves_usi)}

選択する手のUSI記法のみを回答してください（例：7g7f）
説明は不要です。
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"あなたは{player_type}の将棋AIです。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
            temperature=0.5,
        )

        ai_move_usi = response.choices[0].message.content.strip()

        # 生成された手が合法手かチェック
        try:
            ai_move = shogi.Move.from_usi(ai_move_usi)
            if ai_move in legal_moves:
                return ai_move
        except:
            pass

        # 不正な手の場合はランダムに選択
        return random.choice(legal_moves) if legal_moves else None

    except Exception as e:
        print(f"AI手生成エラー: {e}")
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None


async def generate_ai_game(max_moves=30):
    """AI同士の対局を生成"""
    try:
        game_id = f"20250827-{uuid.uuid4().hex[:8]}"

        # プレイヤー設定
        players = {"sente": "宗太郎君 AI", "gote": "四五六君 AI"}

        # AIが有効でない場合はサンプルデータを返す
        if not client:
            print("AIクライアントが無効のため、サンプルデータを使用します")
            print(f"Returning sample data with game_id: {game_id}")
            sample_data = SAMPLE_GAME_DATA.copy()
            sample_data["gameId"] = game_id

            # 要求された手数に合わせてサンプルデータを調整
            if max_moves < len(sample_data["moves"]):
                sample_data["moves"] = sample_data["moves"][:max_moves]
                sample_data["result"] = ""
                sample_data["winReason"] = ""

            return sample_data

        # AI対局を生成
        board = shogi.Board()
        moves = []

        print(f"AI対局を生成中... (最大{max_moves}手)")

        for move_number in range(1, max_moves + 1):
            if board.is_game_over():
                break

            # 現在の手番
            current_player = (
                players["sente"] if board.turn == shogi.BLACK else players["gote"]
            )
            player_type = "先手" if board.turn == shogi.BLACK else "後手"

            print(f"  {move_number}手目を生成中... ({player_type})")

            # AIが手を生成
            ai_move = await generate_ai_move(board, move_number, current_player)

            if ai_move is None:
                print(f"  {move_number}手目: 合法手が見つかりません")
                break

            # 手を適用
            move_usi = ai_move.usi()
            board.push(ai_move)

            # AI解説を生成
            commentary = await generate_ai_commentary(
                board, move_usi, move_number, player_type
            )

            # 手の日本語表記を生成
            move_notation = convert_usi_to_japanese(move_usi, board)

            # 手を記録
            moves.append(
                {
                    "moveNumber": move_number,
                    "moveUsi": move_usi,
                    "moveNotation": move_notation,
                    "commentary": commentary,
                }
            )

            print(f"  {move_number}手目: {move_usi} - {commentary[:30]}...")

            # 少し待機（API制限対策）
            await asyncio.sleep(0.5)

        game_data = {
            "gameId": game_id,
            "sente": players["sente"],
            "gote": players["gote"],
            "moves": moves,
            "result": "",
            "winReason": "",
        }

        print(f"AI対局生成完了: {len(moves)}手")
        return game_data

    except Exception as e:
        print(f"AI対局生成エラー: {e}")
        # エラーの場合はサンプルデータを返す
        sample_data = SAMPLE_GAME_DATA.copy()
        sample_data["gameId"] = f"20250827-{uuid.uuid4().hex[:8]}"
        return sample_data
