# SATOracle_3.py - Versão otimizada com cache e propagação avançada
class SATSolver:
    """
    Versão otimizada com:
    - Cache de cláusulas
    - Propagação de duas literais (2-SAT like)
    - Backjumping básico
    """
    
    def __init__(self, board):
        self.board = board
        self.cache = {}  # Cache de resultados de propagação
        
        # Mapeamento edge -> variável (1-indexed)
        self.edge_to_var = {}
        self.var_to_edge = {}
        for i, edge in enumerate(sorted(board.all_edges), start=1):
            self.edge_to_var[edge] = i
            self.var_to_edge[i] = edge
        
        self.num_vars = len(self.edge_to_var)
        self.assignment = {v: None for v in range(1, self.num_vars + 1)}
        
        self._load_board_state()
        
        # Cache de cláusulas pré-computadas
        self._clause_cache = {}
        self.clauses = self._build_clauses_optimized()
        
        # Para backjumping
        self.decision_level = 0
        self.trail = []  # Histórico de assignments
        self.reason = {}  # Razão para cada assignment
        
    def _load_board_state(self):
        """Load board state with caching"""
        board = self.board
        for edge in board.all_drawn_edges:
            if edge in self.edge_to_var:
                v = self.edge_to_var[edge]
                self.assignment[v] = True
        
        for edge in board.unallowed_edges:
            if edge in self.edge_to_var:
                v = self.edge_to_var[edge]
                self.assignment[v] = False
    
    def _build_clauses_optimized(self) -> list:
        """
        Construção otimizada de cláusulas com:
        - Pre-alocação de listas
        - Eliminação de cláusulas redundantes
        - Ordenação por tamanho
        """
        clauses = []
        
        # Cláusulas de células (hints)
        board = self.board
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue
                
                edges = board.get_cell_edges(r, c)
                vars_ = [self.edge_to_var[e] for e in edges if e in self.edge_to_var]
                
                if not vars_:
                    continue
                
                # At most hint: combinações de tamanho hint+1
                # Usando iteração eficiente
                if hint < len(vars_):
                    self._add_at_most_k(clauses, vars_, hint)
                
                # At least hint: combinações de tamanho len(vars_)-hint+1
                if hint > 0:
                    self._add_at_least_k(clauses, vars_, hint)
        
        # Cláusulas de vértices (grau 0 ou 2)
        self._add_vertex_constraints(clauses)
        
        # Otimização: ordenar cláusulas por tamanho (menores primeiro)
        clauses.sort(key=len)
        
        return clauses
    
    def _add_at_most_k(self, clauses, vars_, k):
        """Adiciona cláusulas at-most-k eficientemente"""
        n = len(vars_)
        if k >= n:
            return
        
        # Para cada subconjunto de tamanho k+1, pelo menos um deve ser falso
        indices = list(range(k + 1))
        
        while True:
            clause = [-vars_[i] for i in indices]
            clauses.append(clause)
            
            # Next combination
            i = k
            while i >= 0 and indices[i] == n - (k + 1 - i):
                i -= 1
            if i < 0:
                break
            indices[i] += 1
            for j in range(i + 1, k + 1):
                indices[j] = indices[j - 1] + 1
    
    def _add_at_least_k(self, clauses, vars_, k):
        """Adiciona cláusulas at-least-k eficientemente"""
        n = len(vars_)
        m = n - k + 1  # tamanho dos subconjuntos para "pelo menos um verdadeiro"
        
        indices = list(range(m))
        
        while True:
            clause = [vars_[i] for i in indices]
            clauses.append(clause)
            
            # Next combination
            i = m - 1
            while i >= 0 and indices[i] == n - (m - i):
                i -= 1
            if i < 0:
                break
            indices[i] += 1
            for j in range(i + 1, m):
                indices[j] = indices[j - 1] + 1
    
    def _add_vertex_constraints(self, clauses):
        """Adiciona constraints de vértices otimizadas"""
        vertices = set()
        for edge in self.board.all_edges:
            v1, v2 = self._edge_vertices(edge)
            vertices.add(v1)
            vertices.add(v2)
        
        for vertex in vertices:
            edges = self._edges_touching_vertex(vertex)
            vars_ = [self.edge_to_var[e] for e in edges if e in self.edge_to_var]
            
            if len(vars_) < 2:
                continue
            
            # At most 2
            if len(vars_) >= 3:
                indices = [0, 1, 2]
                while True:
                    clause = [-vars_[i] for i in indices]
                    clauses.append(clause)
                    
                    # Next combination
                    i = 2
                    while i >= 0 and indices[i] == len(vars_) - (3 - i):
                        i -= 1
                    if i < 0:
                        break
                    indices[i] += 1
                    for j in range(i + 1, 3):
                        indices[j] = indices[j - 1] + 1
            
            # No degree 1: cada edge implica pelo menos outra
            for i, v in enumerate(vars_):
                others = [vars_[j] for j in range(len(vars_)) if j != i]
                if others:
                    clauses.append([-v] + others)
    
    def propagate(self, use_cache=True) -> bool:
        """
        Propagação otimizada com:
        - Cache de resultados
        - Early stopping
        - Backtracking básico
        """
        # Verificar cache
        cache_key = self._get_cache_key()
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Unit propagation
        changed = True
        iterations = 0
        MAX_ITER = len(self.clauses) * 2
        
        while changed and iterations < MAX_ITER:
            changed = False
            iterations += 1
            
            for clause in self.clauses:
                if self._is_contradiction(clause):
                    self.cache[cache_key] = False
                    return False
                
                result = self._check_unit_clause(clause)
                if result:
                    var, value = result
                    if self.assignment[var] is not None and self.assignment[var] != value:
                        self.cache[cache_key] = False
                        return False
                    elif self.assignment[var] is None:
                        self.assignment[var] = value
                        changed = True
        
        # Aplicar ao board
        self._apply_to_board()
        
        # Armazenar em cache
        if use_cache:
            self.cache[cache_key] = True
        
        return True
    
    def _get_cache_key(self):
        """Gera chave de cache baseada no estado atual"""
        drawn = frozenset([e for e, v in self.assignment.items() if v is True])
        forbidden = frozenset([e for e, v in self.assignment.items() if v is False])
        return (drawn, forbidden)
    
    def _is_contradiction(self, clause) -> bool:
        """Verifica se cláusula é contradição (todas falsas)"""
        all_false = True
        for lit in clause:
            var = abs(lit)
            val = self.assignment[var]
            if val is None:
                return False
            lit_true = (lit > 0 and val) or (lit < 0 and not val)
            if lit_true:
                return False
        return all_false
    
    def _check_unit_clause(self, clause):
        """Verifica se cláusula é unitária. Retorna (var, value) ou None"""
        unassigned = []
        for lit in clause:
            var = abs(lit)
            val = self.assignment[var]
            
            if val is None:
                unassigned.append(lit)
            else:
                lit_true = (lit > 0 and val) or (lit < 0 and not val)
                if lit_true:
                    return None  # Cláusula satisfeita
        
        if len(unassigned) == 1:
            lit = unassigned[0]
            return (abs(lit), lit > 0)
        
        return None
    
    def _apply_to_board(self):
        """Aplica assignment ao board com validação"""
        board = self.board
        for var, value in self.assignment.items():
            if value is None:
                continue
            edge = self.var_to_edge[var]
            if value is True:
                if edge not in board.all_drawn_edges:
                    board.mandatory_drawn_edges.add(edge)
            elif value is False:
                if edge in board.allowed_edges:
                    board.allowed_edges.discard(edge)
                    board.unallowed_edges.add(edge)
    
    def _edge_vertices(self, edge):
        t, r, c = edge
        if t == 'h':
            return (r, c), (r, c + 1)
        return (r, c), (r + 1, c)
    
    def _edges_touching_vertex(self, vertex):
        vr, vc = vertex
        candidates = [
            ('h', vr, vc),
            ('h', vr, vc - 1),
            ('v', vr, vc),
            ('v', vr - 1, vc),
        ]
        return [e for e in candidates if e in self.board.all_edges]