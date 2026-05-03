from slitherlink import Board, SlitherlinkState

#class tempate foi feita pelo gemini com prompt 
# "give me a simple class , without meaningfull definitions, 
# just with name and class methods names that make sense theory wise"
# docstrings vieram includas neste template
class ConstraintPropagator:
    """
    Executa o "Forward Checking" e a Consistência de Arcos (AC-3) durante a fase de procura.
    Esta classe 'lê' o estado do tabuleiro e força todas as deduções lógicas antes de 
    devolver o tabuleiro ao algoritmo.
    """

    def __init__(self, state: SlitherlinkState):
        """
        Inicializa o propagador com o estado atual do problema.
        """
        self.state = state
        self.board:Board = state.board
        
        # Uma flag (bandeira) para indicar ao A* se atingimos uma impossibilidade lógica
        # (por exemplo, uma célula com o valor 3 mas que tem apenas 2 arestas disponíveis).
        self.is_valid = True 

    
    # ----- Metodos com logica estatics e inicial caso 3-0 e 0 edges
    def mandatory_edges(self) -> tuple:
        #obter a board list
        board:list = self.board.board
        rows = len(board)
        cols = len(board[0])

        forced_edges = set()
        for r in range(rows):
            for c in range(cols):
                #processamos apenas numa direcao, nao e relevante encontrar
                #3 e 0 na cell1, para depois encontrar 0 e 3 na cell 2. comutativo
                if board[r][c] == 3:
                    #lista com coordenadas de celulas adjacentes
                    a_cells = self.board.adjacent_cell((r, c))
                    for r2, c2 in a_cells:
                        if board[r2][c2] == 0:
                            # 0 acima do 3
                            if r2 < r:
                                forced_edges.update([('h', r + 1, c), ('v', r, c), ('v', r, c + 1)])
                            # 0 abaixo do 3
                            elif r2 > r:
                                forced_edges.update([('h', r, c), ('v', r, c), ('v', r, c + 1)])
                            # 0 a esquerda do 3
                            elif c2 < c:
                                forced_edges.update([('v', r, c + 1), ('h', r, c), ('h', r + 1, c)])
                            # 0 a direita do 3
                            elif c2 > c:
                                forced_edges.update([('v', r, c), ('h', r, c), ('h', r + 1, c)])
        return forced_edges
    
    def unallowed_edges(self) -> tuple:
        #obter a board list
        board:list = self.board.board
        rows = len(board)
        cols = len(board[0])

        forced_edges = set()
        for r in range(rows):
            for c in range(cols):
                # se 0, nenhuma edge a volta e perimitida, assim nao reprocessamos todos
                # os steps da arvore
                if board[r][c] == 0:
                    adjacent_edges = self.board.get_cell_edges(r, c)
                    forced_edges.update(adjacent_edges)
        return forced_edges

