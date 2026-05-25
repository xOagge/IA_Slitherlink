from slitherlink import Board, SlitherlinkState

#class tempate foi feita pelo gemini com prompt 
# "give me a simple class , without meaningfull definitions, 
# just with name and class methods names that make sense theory wise"
# docstrings vieram includas neste template
class InitialPropagator:
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

    #return a todas as mandatory edges
    def mandatory_edges(self) -> tuple:
        return self.case_3_0_edges()[0] | self.mandatory_corner_3_edges() \
             | self.case_3_3_edges()[0] | self.case_3_3_diagonal_edges()[0] \
             | self.mandatory_3_0_diagonal_edges()

    #return a todas as unallowed edges
    def forbidden_edges(self) -> tuple:
        return self.case_3_0_edges()[1] | self.unallowed_0_edges() \
             | self.case_3_3_edges()[1] | self.unallowed_corner_1_edges() \
             | self.case_3_3_diagonal_edges()[1] | self.unallowed_0_1_edges()

    # casos (teem obrigatorios e proibidos), como os relacionamentos, os "casos" sao
    # mais complicados ---------------------------------------------------------
    #return a todas as mandatory edges de acordo com caso 3-0
    def case_3_0_edges(self) -> tuple:
        """quando temos celulas de 3 e 0 adjacentes, temos apenas uma solucao
        que e as edges circundarem o 3, ficando a que esta entre 0 e o 3
        vazia"""
        #obter a board list
        board:list = self.board.board
        rows = len(board)
        cols = len(board[0])

        forced_edges = set()
        forbidden_edges = set()
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
                                forced_edges.update([('h', r+1, c), ('h', r, c-1), ('h', r, c+1), \
                                                     ('v', r, c), ('v', r, c+1)])
                                forbidden_edges.update([('h', r+1, c-1), ('h', r+1, c+1), \
                                                        ('v', r+1, c), ('v', r+1, c+1)])
                            # 0 abaixo do 3
                            elif r2 > r:
                                forced_edges.update([('h', r, c), ('h', r+1, c-1), ('h', r+1, c+1),\
                                                     ('v', r, c), ('v', r, c + 1)])
                                forbidden_edges.update([('h', r, c-1), ('h', r, c+1), \
                                                        ('v', r-1, c), ('v', r-1, c+1)])
                            # 0 a esquerda do 3
                            elif c2 < c:
                                forced_edges.update([('v', r, c+1), ('v', r-1, c), ('v', r+1, c),\
                                                     ('h', r, c), ('h', r + 1, c)])
                                forbidden_edges.update([('h', r, c+1), ('h', r+1, c+1), \
                                                        ('v', r-1, c+1), ('v', r+1, c+1)])
                            # 0 a direita do 3
                            elif c2 > c:
                                forced_edges.update([('v', r, c), ('v', r-1, c+1), ('v', r+1, c+1),\
                                                      ('h', r, c), ('h', r + 1, c)])
                                forbidden_edges.update([('h', r, c-1), ('h', r+1, c-1), \
                                                        ('v', r-1, c), ('v', r+1, c)])
        return forced_edges, forbidden_edges
    
    def case_3_3_diagonal_edges(self) -> tuple:
        #obter a board list
        board:list = self.board.board
        rows = len(board)
        cols = len(board[0])

        #Claude deu esta logica mais simples para as diagonais
        forced_edges = set()
        forbidden_edges = set()
        for r in range(rows):
            for c in range(cols):
                #verificar out of bound
                if r+1 > rows-1 or c+1 > cols-1:
                    continue
                #top left and bottom right, r e c de top left
                if board[r][c] == 3 and board[r+1][c+1] == 3:
                    forced_edges.update([ ('h', r, c), ('v', r, c), \
                                     ('h', r+2, c+1),('v', r+1, c+2),])
                    forbidden_edges.update([ ("h", r, c-1), ("h", r+2, c+2), \
                                             ("v", r-1, c), ("v", r+2, c+2)  ])
                #top right and bottom left, r e c de top left
                if board[r][c+1] == 3 and board[r+1][c] == 3:
                    forced_edges.update([('h', r, c+1), ('v', r, c+2), \
                                        ('h', r+2, c), ('v', r+1, c),])
                    forbidden_edges.update([ ("h", r, c+2), ("h", r+2, c-1), \
                                             ("v", r+2, c), ("v", r-1, c+2)  ])
        return forced_edges, forbidden_edges

    def case_3_3_edges(self) -> tuple:
        """duas celulas com 3 adjacentes leva a duas solucoes com um padrao em
        forma de S, ou S invertido, ambas as solucoes teem a edge entre das duas
        celulas preenchida, e ambas as duas edges mais afastadas"""
        #obter a board list
        board:list = self.board.board
        rows = len(board)
        cols = len(board[0])

        # podia copiar o pensamento de 3_3_diagonal para aquii, mas vou deixar
        #a minha implementacao que inventei de cabeça
        forced_edges = set()
        forbidden_edges = set()
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == 3:
                    #lista com coordenadas de celulas adjacentes
                    a_cells = self.board.adjacent_cell((r, c))
                    for r2, c2 in a_cells:
                        if board[r2][c2] == 3:
                            # cell2 acima da cell1
                            if r2 < r:
                                forced_edges.update([('h', r-1, c), ('h', r, c), ('h', r+1, c)])
                                forbidden_edges.update([('h', r, c-1), ('h', r, c+1)])
                            # cell2 abaixo da cell1
                            elif r2 > r:
                                forced_edges.update([('h', r, c), ('h', r+1, c), ('h', r+2, c)])
                                forbidden_edges.update([('h', r+1, c-1), ('h', r+1, c+1)])
                            # cell2 a esquerda da cell1
                            elif c2 < c:
                                forced_edges.update([('v', r, c-1), ('v', r, c), ('v', r, c+1)])
                                forbidden_edges.update([('v', r-1, c), ('v', r+1, c)])
                            # cell2 a direita da cell1
                            elif c2 > c:
                                forced_edges.update([('v', r, c), ('v', r, c+1), ('v', r, c+2)])
                                forbidden_edges.update([('v', r-1, c+1), ('v', r+1, c+1)])
        return forced_edges, forbidden_edges

    # mandatorys -----------------------
    def mandatory_corner_3_edges(self) -> tuple:
        """Uma celula no canto com um 3 tem duas solucoes, no entanto ambas teem as duas
        edges do canto preenchidas"""
        #obter a board list
        board:list = self.board.board
        rows_i = len(board)-1
        cols_j = len(board[0])-1

        forced_edges = set()
        for r, c in [(0,0), (rows_i,0), (0, cols_j), (rows_i, cols_j)]:
            # cima esquerda
            if board[r][c] == 3 and r == 0 and c == 0:
                forced_edges.update([('h', r, c), ('v', r, c)])
            # cima direita
            if board[r][c] == 3 and r == 0 and c == cols_j:
                forced_edges.update([('h', r, c), ('v', r, cols_j+1)])
            # baixo esquerda
            if board[r][c] == 3 and r == rows_i and c == 0:
                forced_edges.update([('h', rows_i+1, c), ('v', r, c)])
            # baixo direita
            if board[r][c] == 3 and r == rows_i and c == cols_j:
                forced_edges.update([('h', rows_i+1, c), ('v', r, cols_j+1)])
        return forced_edges

    def mandatory_3_0_diagonal_edges(self):
        """caso 3-0 diaognais, que leva a termos duas edges obrigatorias
        as duas edges do 2 mais proximas a celula 0. ChatGPT ajudou a ter o codigo
        com menos identacao"""
        board = self.board.board
        rows = len(board)
        cols = len(board[0])

        forced_edges = set()
        diagonals = [(1,1), (-1,-1), (-1,1), (1,-1)]

        for r in range(rows):
            for c in range(cols):
                #se nao e 3, continuar
                if board[r][c] != 3:
                    continue
                
                for dr, dc in diagonals:
                    r2, c2 = r + dr, c + dc
                    #se out of bound, continuar
                    if not (0 <= r2 < rows and 0 <= c2 < cols):
                        continue
                    #se nao e 0, continuar
                    if board[r2][c2] != 0:
                        continue
                    
                    if dr == 1 and dc == 1: # 0 baixo direita
                        forced_edges.update([('h', r+1, c),('v', r, c+1)])

                    elif dr == 1 and dc == -1: # 0 baixo esquerda
                        forced_edges.update([('h', r+1, c),('v', r, c)])

                    elif dr == -1 and dc == 1: # 0 cima direita
                        forced_edges.update([('h', r, c),('v', r, c+1)])

                    elif dr == -1 and dc == -1: # 0 cima esquerda
                        forced_edges.update([('h', r, c),('v', r, c)])

        return forced_edges


    #unallowed ---------------------
    def unallowed_corner_1_edges(self) -> tuple:
        """Uma celula no canto com um 1 tem duas solucoes, no entanto ambas teem as duas
        edges do canto proibidas"""
        #obter a board list
        board:list = self.board.board
        rows_i = len(board)-1
        cols_j = len(board[0])-1

        forbidden_edges = set()
        for r, c in [(0,0), (rows_i,0), (0, cols_j), (rows_i, cols_j)]:
            # cima esquerda
            if board[r][c] == 1 and r == 0 and c == 0:
                forbidden_edges.update([('h', r, c), ('v', r, c)])
            # cima direita
            if board[r][c] == 1 and r == 0 and c == cols_j:
                forbidden_edges.update([('h', r, c), ('v', r, cols_j+1)])
            # baixo esquerda
            if board[r][c] == 1 and r == rows_i and c == 0:
                forbidden_edges.update([('h', rows_i+1, c), ('v', r, c)])
            # baixo direita
            if board[r][c] == 1 and r == rows_i and c == cols_j:
                forbidden_edges.update([('h', rows_i+1, c), ('v', r, cols_j+1)])
        return forbidden_edges

    def unallowed_0_edges(self) -> tuple:
        #obter a board list
        board:list = self.board.board
        rows = len(board)
        cols = len(board[0])

        forbidden_edges = set()
        for r in range(rows):
            for c in range(cols):
                # se 0, nenhuma edge a volta e perimitida, assim nao reprocessamos todos
                # os steps da arvore
                if board[r][c] == 0:
                    adjacent_edges = self.board.get_cell_edges(r, c)
                    forbidden_edges.update(adjacent_edges)
        return forbidden_edges
    
    def unallowed_0_1_edges(self) -> tuple:
        """1 e 0 na diagonal leva a que todas as edges do 0 e e do 1
        perto do 0 sejam proibidas. vamos apenas dar set a forbidden as 
        edges da celula 1, pois unallowed_0_edges ja trata das edges de 
        todas as celulas 0. Logica e copiada de mandatory_3_0_diagonal_edges,
        basicamente a mesma coisa, mas forbidden"""

        board = self.board.board
        rows = len(board)
        cols = len(board[0])

        forbidden_edges = set()
        diagonals = [(1,1), (-1,-1), (-1,1), (1,-1)]

        for r in range(rows):
            for c in range(cols):
                #se nao e 3, continuar
                if board[r][c] != 1:
                    continue
                
                for dr, dc in diagonals:
                    r2, c2 = r + dr, c + dc
                    #se out of bound, continuar
                    if not (0 <= r2 < rows and 0 <= c2 < cols):
                        continue
                    #se nao e 0, continuar
                    if board[r2][c2] != 0:
                        continue
                    
                    if dr == 1 and dc == 1: # 0 baixo direita
                        forbidden_edges.update([('h', r+1, c),('v', r, c+1)])

                    elif dr == 1 and dc == -1: # 0 baixo esquerda
                        forbidden_edges.update([('h', r+1, c),('v', r, c)])

                    elif dr == -1 and dc == 1: # 0 cima direita
                        forbidden_edges.update([('h', r, c),('v', r, c+1)])

                    elif dr == -1 and dc == -1: # 0 cima esquerda
                        forbidden_edges.update([('h', r, c),('v', r, c)])

        return forbidden_edges
    
    
