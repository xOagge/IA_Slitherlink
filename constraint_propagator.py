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
             | self.mandatory_3_3_edges() | self.case_3_3_diagonal_edges()[0] \
             #| self.case_3_1_3_edges()[0]

    #return a todas as unallowed edges
    def unallowed_edges(self) -> tuple:
        return self.case_3_0_edges()[1] | self.unallowed_0_edges() \
             | self.unallowed_corner_1_edges() | self.case_3_3_diagonal_edges()[1] \
             #| self.case_3_1_3_edges()[1]

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
    
    def mandatory_3_3_edges(self) -> tuple:
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
                            # cell2 abaixo da cell1
                            elif r2 > r:
                                forced_edges.update([('h', r, c), ('h', r+1, c), ('h', r+2, c)])
                            # cell2 a esquerda da cell1
                            elif c2 < c:
                                forced_edges.update([('v', r, c-1), ('v', r, c), ('v', r, c+1)])
                            # cell2 a direita da cell1
                            elif c2 > c:
                                forced_edges.update([('v', r, c), ('v', r, c+1), ('v', r, c+2)])
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

    #gemini fez o codigo, percebi o caso pelo teste 3
    # def case_3_1_3_edges(self) -> tuple:
    #     """quando temos um padrao 3-1-3 (em linha ou coluna), as arestas paralelas 
    #     exteriores dos '3's sao obrigatorias (incluindo as extremidades distantes!), 
    #     e as arestas paralelas do '1' sao proibidas."""
    #     board:list = self.board.board
    #     rows = len(board)
    #     cols = len(board[0])

    #     forced_edges = set()
    #     forbidden_edges = set()
        
    #     for r in range(rows):
    #         for c in range(cols):
    #             # procurar o '1' como ponto central
    #             if board[r][c] == 1:
                    
    #                 # Verificar 3-1-3 Horizontal (3 a esquerda e 3 a direita)
    #                 if c - 1 >= 0 and c + 1 < cols:
    #                     if board[r][c-1] == 3 and board[r][c+1] == 3:
    #                         forced_edges.update([
    #                             ('h', r, c-1), ('h', r+1, c-1),  # Topo e base do 3 esquerdo
    #                             ('v', r, c-1),                   # *** Aresta vertical ESQUERDA do 3 esquerdo ***
    #                             ('h', r, c+1), ('h', r+1, c+1),  # Topo e base do 3 direito
    #                             ('v', r, c+2)                    # *** Aresta vertical DIREITA do 3 direito ***
    #                         ])
    #                         forbidden_edges.update([
    #                             ('h', r, c), ('h', r+1, c)       # Topo e base do 1 central
    #                         ])

    #                 # Verificar 3-1-3 Vertical (3 acima e 3 abaixo)
    #                 if r - 1 >= 0 and r + 1 < rows:
    #                     if board[r-1][c] == 3 and board[r+1][c] == 3:
    #                         forced_edges.update([
    #                             ('v', r-1, c), ('v', r-1, c+1),  # Esq. e dir. do 3 de cima
    #                             ('h', r-1, c),                   # *** Aresta horizontal TOPO do 3 de cima ***
    #                             ('v', r+1, c), ('v', r+1, c+1),  # Esq. e dir. do 3 de baixo
    #                             ('h', r+2, c)                    # *** Aresta horizontal BASE do 3 de baixo ***
    #                         ])
    #                         forbidden_edges.update([
    #                             ('v', r, c), ('v', r, c+1)       # Esq. e dir. do 1 central
    #                         ])

    #     return forced_edges, forbidden_edges


class Propagator:
    """
    Applies deterministic logical rules to a board after each edge placement.
    Call propagate() after every action in result() to resolve all forced moves
    before the search continues.

    Rules applied (in order):
        1. Cell completion  - if active == hint, forbid remaining edges of that cell
        2. Cell forcing     - if available == missing, all available edges are mandatory
        3. Vertex degree    - if degree 2, forbid rest; if degree 1 with one option, force it; if degree 0 with one option, forbid it
        4. Loop prevention  - forbid any edge that would close a loop prematurely

    Returns False if a contradiction is found, True otherwise.
    """

    def __init__(self, board):
        self.board = board

    def propagate(self) -> bool:
        """
        Runs all rules in a loop until stable.
        Returns False if a contradiction is detected, True otherwise.
        """
        changed = True
        while changed:
            changed = False
            changed |= self._rule_cell_completion()
            changed |= self._rule_cell_forcing()
            changed |= self._rule_vertex_degree()
            changed |= self._rule_no_premature_loop()

            if self._has_contradiction():
                return False

            if self._rule_loose_end_reachability():
                return False

        return True

    # --- rules -------------------------------------------------------------------

    def _rule_cell_completion(self) -> bool:
        """
        If active == hint, forbid remaining edges of that cell.
        If active + available == hint, all available edges are mandatory.
        """
        changed = False
        board = self.board

        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue

                active = board.get_active_edges(r, c)
                edges = board.get_cell_edges(r, c)
                available = [e for e in edges
                             if e in board.allowed_edges
                             and e not in board.all_drawn_edges]

                if active == hint:
                    for e in available:
                        board.allowed_edges.discard(e)
                        board.unallowed_edges.add(e)
                        changed = True

                elif active + len(available) == hint:
                    for e in available:
                        if e not in board.mandatory_drawn_edges:
                            board.mandatory_drawn_edges.add(e)
                            changed = True

        return changed

    def _rule_cell_forcing(self) -> bool:
        """
        If the number of available edges equals the number of missing edges,
        all available edges must be drawn.
        """
        changed = False
        board = self.board

        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue

                active = board.get_active_edges(r, c)
                missing = hint - active
                available = [e for e in board.get_cell_edges(r, c)
                             if e in board.allowed_edges
                             and e not in board.all_drawn_edges]

                if missing > 0 and len(available) == missing:
                    for e in available:
                        if e not in board.mandatory_drawn_edges:
                            board.mandatory_drawn_edges.add(e)
                            changed = True

        return changed

    def _rule_vertex_degree(self) -> bool:
        """
        - degree 2: forbid all other edges touching that vertex
        - degree 1: if only one continuation available, force it
        - degree 0: if only one edge available, forbid it (can never reach degree 2)
        """
        changed = False
        board = self.board

        # build degree map
        degree = {}
        for edge in board.all_drawn_edges:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1

        # collect all vertices on the board
        all_vertices = set()
        for edge in board.all_edges:
            for v in self._edge_vertices(edge):
                all_vertices.add(v)

        for v in all_vertices:
            deg = degree.get(v, 0)
            touching = self._edges_touching_vertex(v)
            available = [e for e in touching
                         if e in board.allowed_edges
                         and e not in board.all_drawn_edges]

            if deg == 2:
                for e in available:
                    board.allowed_edges.discard(e)
                    board.unallowed_edges.add(e)
                    changed = True

            elif deg == 1:
                if len(available) == 1:
                    e = available[0]
                    if e not in board.mandatory_drawn_edges:
                        board.mandatory_drawn_edges.add(e)
                        changed = True

            elif deg == 0:
                if len(available) == 1:
                    board.allowed_edges.discard(available[0])
                    board.unallowed_edges.add(available[0])
                    changed = True

        return changed

    def _rule_no_premature_loop(self) -> bool:
        """
        Forbid any edge that would directly connect the two loose ends
        and close the loop unless all hints are already satisfied.
        """
        changed = False
        board = self.board
        drawn = board.all_drawn_edges

        if len(drawn) == 0:
            return False

        degree = {}
        for edge in drawn:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1

        loose_ends = [v for v, deg in degree.items() if deg == 1]

        if len(loose_ends) != 2:
            return False

        v1, v2 = loose_ends

        for e in list(board.allowed_edges - drawn):
            ev1, ev2 = self._edge_vertices(e)
            if {ev1, ev2} == {v1, v2}:
                if not self._all_hints_satisfied():
                    board.allowed_edges.discard(e)
                    board.unallowed_edges.add(e)
                    changed = True

        return changed

    # --- contradiction detection -------------------------------------------------

    def _has_contradiction(self) -> bool:
        """
        Returns True if the board is in an impossible state:
            - a cell has more active edges than its hint
            - a cell cannot possibly reach its hint
            - a vertex has degree > 2
            - a closed sub-loop exists before all hints are satisfied
        """
        board = self.board
        drawn = board.all_drawn_edges

        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue

                active = board.get_active_edges(r, c)
                available = [e for e in board.get_cell_edges(r, c)
                             if e in board.allowed_edges
                             and e not in drawn]

                if active > hint:
                    return True

                if active + len(available) < hint:
                    return True

        # check vertex degrees and detect closed sub-loops
        degree = {}
        for edge in drawn:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1
                if degree[v] > 2:
                    return True

        loose_ends = [v for v, deg in degree.items() if deg == 1]

        if len(loose_ends) == 0 and len(drawn) > 0 and not self._all_hints_satisfied():
            return True

        return False

    def _rule_loose_end_reachability(self) -> bool:
        """
        Returns True (contradiction) if any loose end has no available
        edges to continue from — it is permanently stranded.
        """
        board = self.board
        drawn = board.all_drawn_edges

        if len(drawn) == 0:
            return False

        degree = {}
        for edge in drawn:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1

        loose_ends = [v for v, deg in degree.items() if deg == 1]

        for v in loose_ends:
            touching = self._edges_touching_vertex(v)
            available = [e for e in touching
                         if e in board.allowed_edges
                         and e not in drawn]
            if len(available) == 0:
                return True

        return False

    # --- helpers -----------------------------------------------------------------

    def _edge_vertices(self, edge) -> tuple:
        """Returns the two vertices that an edge connects."""
        t, r, c = edge
        if t == 'h':
            return (r, c), (r, c + 1)
        else:
            return (r, c), (r + 1, c)

    def _edges_touching_vertex(self, vertex) -> list:
        """Returns all valid edges that touch a given vertex."""
        vr, vc = vertex
        candidates = [
            ('h', vr, vc),
            ('h', vr, vc - 1),
            ('v', vr, vc),
            ('v', vr - 1, vc),
        ]
        return [e for e in candidates if e in self.board.all_edges]

    def _all_hints_satisfied(self) -> bool:
        """Returns True if every numbered cell has exactly the right number of active edges."""
        board = self.board
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue
                if board.get_active_edges(r, c) != hint:
                    return False
        return True
    """
    Applies deterministic logical rules to a board after each edge placement.
    Call propagate() after every action in result() to resolve all forced moves
    before the search continues.
    
    Rules applied (in order):
        1. Cell completion  - if active == hint, forbid remaining edges of that cell
        2. Cell forcing     - if available == missing, all available edges are mandatory
        3. Vertex degree    - if a vertex has degree 2, forbid all other edges touching it
        4. Loop prevention  - forbid any edge that would close a loop prematurely
    
    Returns False if a contradiction is found (state is invalid), True otherwise.
    """

    def __init__(self, board):
        self.board = board

    def propagate(self) -> bool:
        """
        Runs all rules in a loop until no more changes occur.
        Returns False if a contradiction is detected, True if stable.
        """
        changed = True
        while changed:
            changed = False
            changed |= self._rule_cell_completion()
            changed |= self._rule_cell_forcing()
            changed |= self._rule_vertex_degree()
            changed |= self._rule_no_premature_loop()
            
            # check for contradictions after each round
            if self._has_contradiction():
                return False
        return True

    # --- rules -------------------------------------------------------------------

    def _rule_cell_completion(self) -> bool:
        """
        If a cell has exactly as many active edges as its hint,
        all remaining edges of that cell are forbidden.
        """
        changed = False
        board = self.board

        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue

                active = board.get_active_edges(r, c)
                if active == hint:
                    for e in board.get_cell_edges(r, c):
                        if e in board.allowed_edges and e not in board.all_drawn_edges:
                            board.allowed_edges.discard(e)
                            board.unallowed_edges.add(e)
                            changed = True

        return changed

    def _rule_cell_forcing(self) -> bool:
        """
        If the number of available edges equals the number of missing edges for a cell,
        all available edges must be drawn.
        """
        changed = False
        board = self.board

        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue

                active = board.get_active_edges(r, c)
                missing = hint - active
                available = [
                    e for e in board.get_cell_edges(r, c)
                    if e in board.allowed_edges and e not in board.all_drawn_edges
                ]

                if missing > 0 and len(available) == missing:
                    for e in available:
                        if e not in board.mandatory_drawn_edges:
                            board.mandatory_drawn_edges.add(e)
                            changed = True

        return changed

    def _rule_vertex_degree(self) -> bool:
        """
        Each vertex can have at most 2 edges.
        If a vertex already has degree 2, forbid all other edges touching it.
        If a vertex has degree 1 and only 1 available edge remains, that edge is mandatory.
        """
        changed = False
        board = self.board

        # build degree map for all vertices
        degree = {}
        for edge in board.all_drawn_edges:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1

        # for each vertex, apply rules
        for v, deg in degree.items():
            touching = self._edges_touching_vertex(v)

            if deg == 2:
                # vertex is full, forbid everything else
                for e in touching:
                    if e in board.allowed_edges and e not in board.all_drawn_edges:
                        board.allowed_edges.discard(e)
                        board.unallowed_edges.add(e)
                        changed = True

            elif deg == 1:
                # loose end: if only one continuation available, it is forced
                available = [
                    e for e in touching
                    if e in board.allowed_edges and e not in board.all_drawn_edges
                ]
                if len(available) == 1:
                    e = available[0]
                    if e not in board.mandatory_drawn_edges:
                        board.mandatory_drawn_edges.add(e)
                        changed = True

        return changed

    def _rule_no_premature_loop(self) -> bool:
        """
        Forbid any edge that would close the current path into a loop
        unless every cell hint is already satisfied (i.e. it would be the solution).
        """
        changed = False
        board = self.board
        drawn = board.all_drawn_edges

        if len(drawn) == 0:
            return False

        # find the two loose ends (degree-1 vertices)
        degree = {}
        for edge in drawn:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1

        loose_ends = [v for v, deg in degree.items() if deg == 1]

        # a loop closes when the two loose ends are connected
        # this only makes sense if there are exactly 2 loose ends
        if len(loose_ends) != 2:
            return False

        v1, v2 = loose_ends

        # check if any single edge directly connects the two loose ends
        for e in list(board.allowed_edges - drawn):
            verts = self._edge_vertices(e)
            if set(verts) == {v1, v2}:
                # this edge would close the loop - only allow if all hints satisfied
                if not self._all_hints_satisfied():
                    board.allowed_edges.discard(e)
                    board.unallowed_edges.add(e)
                    changed = True

        return changed

    # --- contradiction detection -------------------------------------------------

    def _has_contradiction(self) -> bool:
        board = self.board
        drawn = board.all_drawn_edges

        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue

                active = board.get_active_edges(r, c)
                available = [
                    e for e in board.get_cell_edges(r, c)
                    if e in board.allowed_edges and e not in drawn
                ]

                if active > hint:
                    return True

                if active + len(available) < hint:
                    return True

        # check vertex degrees and find loose ends in one pass
        degree = {}
        for edge in drawn:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1
                if degree[v] > 2:
                    return True

        loose_ends = [v for v, deg in degree.items() if deg == 1]

        # closed sub-loop detected before solution is complete
        if len(loose_ends) == 0 and len(drawn) > 0 and not self._all_hints_satisfied():
            return True

        return False
    
    # --- helpers -----------------------------------------------------------------

    def _edge_vertices(self, edge) -> tuple:
        """Returns the two vertices (points) that an edge connects."""
        t, r, c = edge
        if t == 'h':
            return (r, c), (r, c + 1)
        else:  # 'v'
            return (r, c), (r + 1, c)

    def _edges_touching_vertex(self, vertex) -> list:
        """Returns all possible edges that touch a given vertex."""
        vr, vc = vertex
        candidates = [
            ('h', vr, vc),
            ('h', vr, vc - 1),
            ('v', vr, vc),
            ('v', vr - 1, vc),
        ]
        return [e for e in candidates if e in self.board.all_edges]

    def _all_hints_satisfied(self) -> bool:
        """Returns True if every numbered cell has exactly the right number of active edges."""
        board = self.board
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue
                if board.get_active_edges(r, c) != hint:
                    return False
        return True
    
    def _rule_no_premature_loop(self) -> bool:
        changed = False
        board = self.board
        drawn = board.all_drawn_edges

        if len(drawn) == 0:
            return False

        # build degree map
        degree = {}
        for edge in drawn:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1

        loose_ends = [v for v, deg in degree.items() if deg == 1]

        # if there are NO loose ends but hints arent all satisfied,
        # we already have an illegal closed loop — contradiction
        if len(loose_ends) == 0 and not self._all_hints_satisfied():
            return False  # _has_contradiction will catch this via hint check

        if len(loose_ends) != 2:
            return False

        v1, v2 = loose_ends

        # forbid any edge that directly connects the two loose ends
        # unless all hints are satisfied
        for e in list(board.allowed_edges - drawn):
            verts = set(self._edge_vertices(e))
            if verts == {v1, v2}:
                if not self._all_hints_satisfied():
                    board.allowed_edges.discard(e)
                    board.unallowed_edges.add(e)
                    changed = True

        return changed
    

    
    def _rule_loose_end_reachability(self) -> bool:
        board = self.board
        drawn = board.all_drawn_edges

        if len(drawn) == 0:
            return False

        degree = {}
        for edge in drawn:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1

        loose_ends = [v for v, deg in degree.items() if deg == 1]

        for v in loose_ends:
            touching = self._edges_touching_vertex(v)
            available = [e for e in touching
                        if e in board.allowed_edges
                        and e not in drawn]
            if len(available) == 0:
                return True  # signal contradiction to propagate()
        
        return False
    
    def _rule_cell_completion(self) -> bool:
        changed = False
        board = self.board

        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue

                active = board.get_active_edges(r, c)
                edges = board.get_cell_edges(r, c)
                available = [e for e in edges 
                            if e in board.allowed_edges 
                            and e not in board.all_drawn_edges]

                if active == hint:
                    for e in available:
                        board.allowed_edges.discard(e)
                        board.unallowed_edges.add(e)
                        changed = True

                # if remaining available + active still cant reach hint, contradiction
                # (already in _has_contradiction but catch early here too)
                elif active + len(available) == hint:
                    for e in available:
                        if e not in board.mandatory_drawn_edges:
                            board.mandatory_drawn_edges.add(e)
                            changed = True

        return changed

    def _rule_no_premature_loop(self) -> bool:
        changed = False
        board = self.board
        drawn = board.all_drawn_edges

        if len(drawn) == 0:
            return False

        degree = {}
        for edge in drawn:
            for v in self._edge_vertices(edge):
                degree[v] = degree.get(v, 0) + 1

        loose_ends = [v for v, deg in degree.items() if deg == 1]

        if len(loose_ends) == 0 and not self._all_hints_satisfied():
            return False  # already a contradiction

        if len(loose_ends) != 2:
            return False

        v1, v2 = loose_ends

        for e in list(board.allowed_edges - drawn):
            ev1, ev2 = self._edge_vertices(e)
            # this edge connects the two loose ends directly -> closes the loop
            if set([ev1, ev2]) == {v1, v2}:
                if not self._all_hints_satisfied():
                    board.allowed_edges.discard(e)
                    board.unallowed_edges.add(e)
                    changed = True

        return changed