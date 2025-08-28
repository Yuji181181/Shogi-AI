// 棋譜ビューアのJavaScript

class ShogiViewer {
    constructor() {
        this.gameData = null;
        this.currentMoveIndex = 0;
        this.boardStates = [];
        this.isLoading = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadGameData();
    }

    initializeElements() {
        // DOM要素の取得
        this.gameIdElement = document.getElementById('gameId');
        this.sentePlayerElement = document.getElementById('sentePlayer');
        this.gotePlayerElement = document.getElementById('gotePlayer');
        this.boardTextElement = document.getElementById('boardText');
        this.currentMoveNumberElement = document.getElementById('currentMoveNumber');
        this.currentTurnElement = document.getElementById('currentTurn');
        this.senteCapturedElement = document.getElementById('senteCaptured');
        this.goteCapturedElement = document.getElementById('goteCaptured');
        this.movesListElement = document.getElementById('movesList');
        this.commentaryDisplayElement = document.getElementById('commentaryDisplay');
        this.gameResultElement = document.getElementById('gameResult');
        
        // ボタン要素
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.firstBtn = document.getElementById('firstBtn');
        this.lastBtn = document.getElementById('lastBtn');
        this.backToHomeBtn = document.getElementById('backToHomeBtn');
        this.downloadKifuBtn = document.getElementById('downloadKifuBtn');
    }

    bindEvents() {
        // ナビゲーションボタン
        this.prevBtn.addEventListener('click', () => this.previousMove());
        this.nextBtn.addEventListener('click', () => this.nextMove());
        this.firstBtn.addEventListener('click', () => this.goToMove(0));
        this.lastBtn.addEventListener('click', () => this.goToMove(this.gameData?.moves.length || 0));
        
        // その他のボタン
        this.backToHomeBtn.addEventListener('click', () => window.location.href = '/');
        this.downloadKifuBtn.addEventListener('click', () => this.downloadKifu());
        
        // キーボードショートカット
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousMove();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextMove();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.goToMove(0);
                    break;
                case 'End':
                    e.preventDefault();
                    this.goToMove(this.gameData?.moves.length || 0);
                    break;
            }
        });
    }

    async loadGameData() {
        try {
            // セッションストレージからゲームデータを取得
            const storedData = sessionStorage.getItem('currentGameData');
            if (!storedData) {
                throw new Error('ゲームデータが見つかりません');
            }

            this.gameData = JSON.parse(storedData);
            this.initializeGame();
            
        } catch (error) {
            console.error('Error loading game data:', error);
            this.showError('ゲームデータの読み込みに失敗しました');
        }
    }

    initializeGame() {
        if (!this.gameData) return;

        // ゲーム情報の表示
        this.gameIdElement.textContent = this.gameData.gameId;
        this.sentePlayerElement.textContent = this.gameData.sente;
        this.gotePlayerElement.textContent = this.gameData.gote;

        // 対局結果の表示は無効化（常に表示されてしまうため）
        // if (this.gameData.result && this.gameResultElement) {
        //     this.gameResultElement.style.display = 'block';
        //     const resultText = `${this.gameData.result}（${this.gameData.winReason || ''}）`;
        //     this.gameResultElement.querySelector('.result-text').textContent = resultText;
        // }

        // 棋譜リストの生成
        this.generateMovesList();

        // 初期位置（0手目）を表示
        this.goToMove(0);
    }

    generateMovesList() {
        if (!this.gameData || !this.gameData.moves) return;

        this.movesListElement.innerHTML = '';

        // 初期局面
        const initialMoveItem = this.createMoveElement(0, '初期局面', '対局開始時の盤面です');
        this.movesListElement.appendChild(initialMoveItem);

        // 各手の表示
        this.gameData.moves.forEach((move, index) => {
            // moveNotationがある場合はそれを使用、なければmoveUsiを使用
            const notation = move.moveNotation || move.moveUsi;
            const moveItem = this.createMoveElement(
                move.moveNumber,
                notation,
                move.commentary.substring(0, 30) + '...'
            );
            this.movesListElement.appendChild(moveItem);
        });
    }

    createMoveElement(moveNumber, notation, preview) {
        const moveItem = document.createElement('div');
        moveItem.className = 'move-item';
        moveItem.dataset.moveIndex = moveNumber;

        const moveNumberDiv = document.createElement('div');
        moveNumberDiv.className = 'move-number';
        moveNumberDiv.textContent = moveNumber;

        const moveNotationDiv = document.createElement('div');
        moveNotationDiv.className = 'move-notation';
        moveNotationDiv.textContent = notation;

        const movePreviewDiv = document.createElement('div');
        movePreviewDiv.className = 'move-preview';
        movePreviewDiv.textContent = preview;

        moveItem.appendChild(moveNumberDiv);
        moveItem.appendChild(moveNotationDiv);
        moveItem.appendChild(movePreviewDiv);

        // クリックイベント
        moveItem.addEventListener('click', () => {
            this.goToMove(parseInt(moveItem.dataset.moveIndex));
        });

        return moveItem;
    }

    async goToMove(moveIndex) {
        if (this.isLoading) return;
        
        const maxMoves = this.gameData ? this.gameData.moves.length : 0;
        moveIndex = Math.max(0, Math.min(moveIndex, maxMoves));
        
        this.currentMoveIndex = moveIndex;
        
        try {
            this.isLoading = true;
            await this.updateBoardDisplay(moveIndex);
            this.updateMoveHighlight();
            this.updateNavigationButtons();
            this.updateCommentary();
            
        } catch (error) {
            console.error('Error updating move:', error);
            this.showError('盤面の更新に失敗しました');
        } finally {
            this.isLoading = false;
        }
    }

    async updateBoardDisplay(moveIndex) {
        try {
            // API から盤面状態を取得
            const gameId = this.gameData.gameId;
            const response = await fetch(`/api/board_state/${gameId}/${moveIndex}`);
            const data = await response.json();

            if (data.success) {
                // 盤面表示の更新（後手駒の色分けマーカーを処理）
                let boardHtml = data.boardState;
                // 後手の駒マーカー（◆駒名◆）を赤色のspanに置換
                boardHtml = boardHtml.replace(/◆([^◆]+)◆/g, '<span class="gote-piece">$1</span>');
                this.boardTextElement.innerHTML = boardHtml;
                
                // 手数と手番の更新
                this.currentMoveNumberElement.textContent = moveIndex;
                this.currentTurnElement.textContent = data.currentTurn;
                this.currentTurnElement.className = `turn-indicator ${data.currentTurn === '先手' ? 'sente' : 'gote'}`;

                // 持ち駒の更新
                this.updateCapturedPieces(data.capturedPieces);
                
            } else {
                throw new Error(data.error || '盤面データの取得に失敗');
            }
            
        } catch (error) {
            console.error('Error fetching board state:', error);
            this.boardTextElement.innerHTML = 'エラー: 盤面を表示できません';
        }
    }

    updateCapturedPieces(capturedPieces) {
        // 先手の持ち駒
        this.senteCapturedElement.innerHTML = '';
        if (capturedPieces.sente && Object.keys(capturedPieces.sente).length > 0) {
            Object.entries(capturedPieces.sente).forEach(([piece, count]) => {
                const pieceElement = document.createElement('span');
                pieceElement.className = 'captured-piece';
                pieceElement.textContent = count > 1 ? `${piece}×${count}` : piece;
                this.senteCapturedElement.appendChild(pieceElement);
            });
        } else {
            this.senteCapturedElement.textContent = 'なし';
        }

        // 後手の持ち駒
        this.goteCapturedElement.innerHTML = '';
        if (capturedPieces.gote && Object.keys(capturedPieces.gote).length > 0) {
            Object.entries(capturedPieces.gote).forEach(([piece, count]) => {
                const pieceElement = document.createElement('span');
                pieceElement.className = 'captured-piece';
                pieceElement.textContent = count > 1 ? `${piece}×${count}` : piece;
                this.goteCapturedElement.appendChild(pieceElement);
            });
        } else {
            this.goteCapturedElement.textContent = 'なし';
        }
    }

    updateMoveHighlight() {
        // 全ての手のハイライトを除去
        document.querySelectorAll('.move-item').forEach(item => {
            item.classList.remove('active');
        });

        // 現在の手をハイライト
        const currentMoveElement = document.querySelector(`[data-move-index="${this.currentMoveIndex}"]`);
        if (currentMoveElement) {
            currentMoveElement.classList.add('active');
            currentMoveElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    updateNavigationButtons() {
        const maxMoves = this.gameData ? this.gameData.moves.length : 0;
        
        this.prevBtn.disabled = this.currentMoveIndex <= 0;
        this.firstBtn.disabled = this.currentMoveIndex <= 0;
        this.nextBtn.disabled = this.currentMoveIndex >= maxMoves;
        this.lastBtn.disabled = this.currentMoveIndex >= maxMoves;
    }

    updateCommentary() {
        if (this.currentMoveIndex === 0) {
            this.commentaryDisplayElement.textContent = '対局開始時の盤面です。これから宗太郎君AIと四五六君AIによる対局が始まります。';
        } else if (this.gameData && this.gameData.moves[this.currentMoveIndex - 1]) {
            const move = this.gameData.moves[this.currentMoveIndex - 1];
            this.commentaryDisplayElement.textContent = move.commentary;
        } else {
            this.commentaryDisplayElement.textContent = '解説データがありません';
        }
    }

    previousMove() {
        if (this.currentMoveIndex > 0) {
            this.goToMove(this.currentMoveIndex - 1);
        }
    }

    nextMove() {
        const maxMoves = this.gameData ? this.gameData.moves.length : 0;
        if (this.currentMoveIndex < maxMoves) {
            this.goToMove(this.currentMoveIndex + 1);
        }
    }

    downloadKifu() {
        if (!this.gameData) {
            this.showError('ダウンロードするデータがありません');
            return;
        }

        try {
            // 棋譜データをテキスト形式で生成
            let kifuText = `# ${this.gameData.sente} vs ${this.gameData.gote}\n`;
            kifuText += `# 対局ID: ${this.gameData.gameId}\n`;
            kifuText += `# 生成日時: ${new Date().toLocaleString()}\n\n`;

            this.gameData.moves.forEach((move, index) => {
                kifuText += `${move.moveNumber}. ${move.moveUsi}\n`;
                kifuText += `   ${move.commentary}\n\n`;
            });

            // ダウンロード
            const blob = new Blob([kifuText], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `kifu_${this.gameData.gameId}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

        } catch (error) {
            console.error('Error downloading kifu:', error);
            this.showError('棋譜のダウンロードに失敗しました');
        }
    }

    showError(message) {
        // 簡単なエラー表示
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.position = 'fixed';
        errorDiv.style.top = '20px';
        errorDiv.style.right = '20px';
        errorDiv.style.zIndex = '1000';
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
}

// ページ読み込み時にビューアを初期化
document.addEventListener('DOMContentLoaded', function() {
    new ShogiViewer();
});

// ページの視覚効果
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    container.style.opacity = '0';
    container.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        container.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
    }, 100);
});
