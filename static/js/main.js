// メインページのJavaScript

document.addEventListener('DOMContentLoaded', function() {
    const startGameBtn = document.getElementById('startGameBtn');
    const loadingMessage = document.getElementById('loadingMessage');
    const errorMessage = document.getElementById('errorMessage');
    const maxMovesSelect = document.getElementById('maxMovesSelect');
    const selectedMovesSpan = document.getElementById('selectedMoves');

    // 手数選択の変更イベント
    maxMovesSelect.addEventListener('change', function() {
        const selectedMoves = this.value;
        selectedMovesSpan.textContent = selectedMoves + '手';
    });

    startGameBtn.addEventListener('click', async function() {
        try {
            // 選択された手数を取得
            const maxMoves = parseInt(maxMovesSelect.value);
            
            // UIの更新
            startGameBtn.style.display = 'none';
            loadingMessage.style.display = 'block';
            errorMessage.style.display = 'none';

            // 対局開始APIを呼び出し
            const response = await fetch('/api/start_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    maxMoves: maxMoves
                })
            });

            const data = await response.json();

            if (data.success) {
                // 成功時は棋譜ビューアに遷移
                // ゲームデータをセッションストレージに保存
                sessionStorage.setItem('currentGameData', JSON.stringify(data.gameData));
                
                // ビューアページに遷移
                window.location.href = '/viewer';
            } else {
                throw new Error(data.error || '対局の生成に失敗しました');
            }

        } catch (error) {
            console.error('Error starting game:', error);
            
            // エラー表示
            loadingMessage.style.display = 'none';
            errorMessage.style.display = 'block';
            errorMessage.textContent = `エラーが発生しました: ${error.message}`;
            startGameBtn.style.display = 'inline-block';
        }
    });

    // エラーメッセージをクリックで隠す
    errorMessage.addEventListener('click', function() {
        errorMessage.style.display = 'none';
    });
});

// ページの視覚効果
document.addEventListener('DOMContentLoaded', function() {
    // フェードイン効果
    const container = document.querySelector('.container');
    container.style.opacity = '0';
    container.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        container.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
    }, 100);

    // プレイヤーアバターのアニメーション
    const avatars = document.querySelectorAll('.player-avatar');
    avatars.forEach((avatar, index) => {
        avatar.style.animation = `bounce 2s ease-in-out infinite ${index * 0.5}s`;
    });
});

// CSSアニメーションをJavaScriptで定義
const style = document.createElement('style');
style.textContent = `
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
        }
    }
    
    .start-btn {
        animation: pulse 2s infinite;
    }
`;
document.head.appendChild(style);
