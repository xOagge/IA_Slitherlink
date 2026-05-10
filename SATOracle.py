class SATSolver:
    """
    Solves Slitherlink constraints using SAT (Boolean Satisfiability) logic.
    
    Each edge is a boolean variable: True = drawn, False = forbidden.
    Constraints are encoded as clauses and solved via unit propagation (DPLL-lite).
    
    No imports needed - pure Python boolean logic.
    
    Variables:
        Each edge in board.all_edges gets a unique integer ID.
        Positive ID = edge must be drawn.
        Negative ID = edge must NOT be drawn.
    
    Clauses:
        Lists of integers (literals). A clause is satisfied if at least one
        literal is True. Unit clause = only one literal left = forced assignment.
    """

    def __init__(self, board):
        self.board = board

        # map each edge to a unique integer ID (1-indexed for SAT convention)
        self.edge_to_var = {}
        self.var_to_edge = {}
        for i, edge in enumerate(sorted(board.all_edges), start=1):
            self.edge_to_var[edge] = i
            self.var_to_edge[i] = edge

        self.num_vars = len(self.edge_to_var)

        # assignment: var -> True/False/None
        self.assignment = {v: None for v in range(1, self.num_vars + 1)}

        # load current board state into assignment
        self._load_board_state()

        # build all clauses from the puzzle constraints
        self.clauses = self._build_clauses()

    # --- setup -------------------------------------------------------------------

    def _load_board_state(self):
        """Seed the SAT assignment from what the board already knows."""
        board = self.board
        for edge in board.all_drawn_edges:
            if edge in self.edge_to_var:
                v = self.edge_to_var[edge]
                self.assignment[v] = True

        for edge in board.unallowed_edges:
            if edge in self.edge_to_var:
                v = self.edge_to_var[edge]
                self.assignment[v] = False

    def _build_clauses(self) -> list:
        """
        Encode all Slitherlink rules as SAT clauses.
        Returns a list of clauses, each clause is a list of integer literals.
        """
        clauses = []
        clauses += self._clauses_cell_hints()
        clauses += self._clauses_vertex_degree()
        return clauses

    # --- constraint encoding -----------------------------------------------------

    def _clauses_cell_hints(self) -> list:
        """
        For each numbered cell, encode that exactly N of its 4 edges are True.

        Exactly-N is encoded as:
            - At least N  (if fewer than N are true, at least one more must be)
            - At most N   (if N are true, none of the rest can be)

        We use a simplified encoding:
            At most N:  for every subset of size N+1, at least one must be False
            At least N: for every subset of size (4-N+1), at least one must be True
        """
        clauses = []
        board = self.board

        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue

                edges = board.get_cell_edges(r, c)
                vars_ = [self.edge_to_var[e] for e in edges if e in self.edge_to_var]

                # at most hint: no subset of size hint+1 can all be True
                for combo in self._combinations(vars_, hint + 1):
                    # at least one of these must be False = at least one negative literal
                    clauses.append([-v for v in combo])

                # at least hint: no subset of size (len-hint+1) can all be False
                for combo in self._combinations(vars_, len(vars_) - hint + 1):
                    # at least one of these must be True = at least one positive literal
                    clauses.append([v for v in combo])

        return clauses

    def _clauses_vertex_degree(self) -> list:
        """
        For each vertex, encode that exactly 0 or 2 of its edges are True.
        (A vertex is either not used, or used with degree exactly 2.)

        This is harder to encode purely in SAT without auxiliary variables.
        We use the simpler necessary condition:
            - At most 2 edges per vertex (no degree > 2)
            - If any edge at a vertex is True, at least one other must also be True
              (no degree 1 - no loose ends)
        """
        clauses = []
        board = self.board

        # collect all vertices
        all_vertices = set()
        for edge in board.all_edges:
            for v in self._edge_vertices(edge):
                all_vertices.add(v)

        for vertex in all_vertices:
            touching = self._edges_touching_vertex(vertex)
            vars_ = [self.edge_to_var[e] for e in touching if e in self.edge_to_var]

            if len(vars_) < 2:
                continue

            # at most 2: no subset of 3 can all be True
            for combo in self._combinations(vars_, 3):
                clauses.append([-v for v in combo])

            # no degree 1: if edge A is True, at least one other edge at this vertex is True
            # encoded as: for each var v, (-v OR v2 OR v3 OR ...)
            for i, v in enumerate(vars_):
                others = [vars_[j] for j in range(len(vars_)) if j != i]
                if others:
                    # if v is True, at least one other must be True
                    clauses.append([-v] + others)

        return clauses

    # --- unit propagation (the core SAT engine) ----------------------------------

    def propagate(self) -> bool:
        """
        Runs unit propagation: if a clause has only one unassigned literal,
        that literal is forced. Repeat until stable or contradiction found.

        Returns True if stable (no contradiction), False if contradiction found.
        Then writes forced assignments back to the board.
        """
        changed = True
        while changed:
            changed = False

            for clause in self.clauses:
                # evaluate clause against current assignment
                status, unassigned = self._evaluate_clause(clause)

                if status == 'satisfied':
                    continue

                if status == 'contradiction':
                    return False

                if status == 'unit':
                    # only one literal left unassigned - force it
                    lit = unassigned[0]
                    var = abs(lit)
                    value = lit > 0  # positive literal = True, negative = False

                    if self.assignment[var] is not None:
                        # already assigned - check consistency
                        if self.assignment[var] != value:
                            return False
                    else:
                        self.assignment[var] = value
                        changed = True

        # write results back to board
        self._apply_to_board()
        return True

    def _evaluate_clause(self, clause) -> tuple:
        """
        Evaluates a clause against current assignment.

        Returns:
            ('satisfied', [])           - at least one literal is True
            ('contradiction', [])       - all literals are False
            ('unit', [unassigned_lit])  - exactly one literal unassigned, rest False
            ('unresolved', [...])       - multiple literals unassigned
        """
        unassigned = []

        for lit in clause:
            var = abs(lit)
            val = self.assignment[var]

            if val is None:
                unassigned.append(lit)
            else:
                # literal is True if (positive and assigned True) or (negative and assigned False)
                lit_true = (lit > 0 and val) or (lit < 0 and not val)
                if lit_true:
                    return 'satisfied', []

        if len(unassigned) == 0:
            return 'contradiction', []
        elif len(unassigned) == 1:
            return 'unit', unassigned
        else:
            return 'unresolved', unassigned

    # --- write results back to board ---------------------------------------------

    def _apply_to_board(self):
        """
        Writes the SAT assignment back to the board as mandatory/forbidden edges.
        """
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

    # --- helpers -----------------------------------------------------------------

    def _edge_vertices(self, edge) -> tuple:
        """Returns the two vertices that an edge connects."""
        t, r, c = edge
        if t == 'h':
            return (r, c), (r, c + 1)
        else:
            return (r, c), (r + 1, c)

    def _edges_touching_vertex(self, vertex) -> list:
        """Returns all valid edges touching a vertex."""
        vr, vc = vertex
        candidates = [
            ('h', vr, vc),
            ('h', vr, vc - 1),
            ('v', vr, vc),
            ('v', vr - 1, vc),
        ]
        return [e for e in candidates if e in self.board.all_edges]

    def _combinations(self, items, r) -> list:
        """
        Returns all combinations of `items` of size `r`.
        Pure Python, no imports.
        """
        if r == 0:
            return [[]]
        if r > len(items):
            return []
        result = []
        for i in range(len(items)):
            rest = self._combinations(items[i+1:], r - 1)
            for combo in rest:
                result.append([items[i]] + combo)
        return result