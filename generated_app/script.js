const board = document.getElementById('chessboard');
const rows = 8;
const cols = 8;
const pieces = {
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'
};
let currentPlayer = 'white'; // White starts first

// Initialize the chessboard
function initBoard() {
    for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
            const square = document.createElement('div');
            square.className = 'square ' + ((i + j) % 2 === 0 ? 'white' : 'black');
            square.dataset.position = `${i},${j}`;
            board.appendChild(square);
        }
    }
}

// Place pieces on the board
function setupPieces() {
    const initialPositions = [
        "rnbqkbnr",
        "pppppppp",
        "        ",
        "        ",
        "        ",
        "        ",
        "PPPPPPPP",
        "RNBQKBNR"
    ];

    for (let i = 0; i < initialPositions.length; i++) {
        for (let j = 0; j < initialPositions[i].length; j++) {
            const piece = initialPositions[i][j];
            if (piece !== ' ') {
                const square = board.children[i * cols + j];
                const pieceElement = document.createElement('span');
                pieceElement.className = 'piece';
                pieceElement.textContent = pieces[piece];
                pieceElement.dataset.pieceType = piece;
                pieceElement.draggable = true;
                square.appendChild(pieceElement);
            }
        }
    }
}

function enableDrag() {
    const pieces = document.querySelectorAll('.piece');
    pieces.forEach(piece => {
        piece.addEventListener('dragstart', handleDragStart);
    });

    const squares = document.querySelectorAll('#chessboard .square');
    squares.forEach(square => {
        square.addEventListener('dragover', handleDragOver);
        square.addEventListener('drop', handleDrop);
    });
}

function handleDragStart(e) {
    if ((currentPlayer === 'white' && e.target.dataset.pieceType === e.target.dataset.pieceType.toUpperCase()) ||
        (currentPlayer === 'black' && e.target.dataset.pieceType === e.target.dataset.pieceType.toLowerCase())) {
        e.dataTransfer.setData('text/plain', e.target.dataset.pieceType);
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setDragImage(e.target, 25, 25);
        e.target.classList.add('dragging');
    } else {
        e.preventDefault(); // Prevent drag if not the player's turn
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDrop(e) {
    e.preventDefault();
    const pieceType = e.dataTransfer.getData('text/plain');
    const targetSquare = e.target.closest('.square');
    const draggingPiece = document.querySelector('.dragging');
    if (targetSquare && isValidMove(draggingPiece, targetSquare)) {
        targetSquare.textContent = ''; // Clear the target square
        targetSquare.appendChild(draggingPiece);
        draggingPiece.classList.remove('dragging');
        togglePlayer(); // Switch turns after a successful move
    }
}

function isValidMove(piece, targetSquare) {
    const sourcePosition = piece.parentNode.dataset.position.split(',').map(Number);
    const targetPosition = targetSquare.dataset.position.split(',').map(Number);
    const pieceType = piece.dataset.pieceType.toLowerCase();
    const isWhite = piece.dataset.pieceType === piece.dataset.pieceType.toUpperCase();
    const rowDiff = targetPosition[0] - sourcePosition[0];
    const colDiff = targetPosition[1] - sourcePosition[1];

    // Implement basic movement rules for each piece
    switch (pieceType) {
        case 'p': // Pawn
            if (isWhite) {
                if (sourcePosition[0] === 6 && rowDiff === -2 && colDiff === 0) return true; // Initial double move
                if (rowDiff === -1 && colDiff === 0) return true; // Normal forward move
            } else {
                if (sourcePosition[0] === 1 && rowDiff === 2 && colDiff === 0) return true; // Initial double move
                if (rowDiff === 1 && colDiff === 0) return true; // Normal forward move
            }
            break;
        case 'r': // Rook
            if (rowDiff === 0 || colDiff === 0) return true;
            break;
        case 'n': // Knight
            if ((Math.abs(rowDiff) === 2 && Math.abs(colDiff) === 1) ||
                (Math.abs(rowDiff) === 1 && Math.abs(colDiff) === 2)) return true;
            break;
        case 'b': // Bishop
            if (Math.abs(rowDiff) === Math.abs(colDiff)) return true;
            break;
        case 'q': // Queen
            if (Math.abs(rowDiff) === Math.abs(colDiff) || rowDiff === 0 || colDiff === 0) return true;
            break;
        case 'k': // King
            if (Math.abs(rowDiff) <= 1 && Math.abs(colDiff) <= 1) return true;
            break;
    }
    return false;
}

function togglePlayer() {
    currentPlayer = (currentPlayer === 'white') ? 'black' : 'white';
    document.getElementById('turn').textContent = `Current Turn: ${currentPlayer}`;
}

// Initialize game
initBoard();
setupPieces();
enableDrag();