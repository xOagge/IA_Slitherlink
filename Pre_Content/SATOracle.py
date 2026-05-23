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

    Cache:
        The solver caches propagation results keyed by a frozen snapshot of the
        board state (drawn edges + forbidden edges).  When the search visits the
        same partial state again — which happens constantly in regions where the
        loop is forced through a corridor — the cached result is returned
        immediately instead of re-running the full propagation.

        Cache format:
            _propagation_cache[state_key] = (valid: bool,
                                             new_mandatory: frozenset,
                                             new_forbidden: frozenset)

        The cache is a CLASS-LEVEL attribute so it persists across every
        SATSolver instance created during a single search run.
    """

    # ------------------------------------------------------------------
    # Class-level cache shared across ALL instances in one search run.
    # Key   : (frozenset of drawn edges, frozenset of forbidden edges)
    # Value : (valid: bool, extra_mandatory: frozenset, extra_forbidden: frozenset)
    # ------------------------------------------------------------------
    _propagation_cache: dict = {}

    @classmethod
    def clear_cache(cls):
        """Call this between independent puzzle runs to free memory."""
        cls._propagation_cache.clear()

    # ------------------------------------------------------------------

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
                    clauses.append([-v for v in combo])

                # at least hint: no subset of size (len-hint+1) can all be False
                for combo in self._combinations(vars_, len(vars_) - hint + 1):
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
            for i, v in enumerate(vars_):
                others = [vars_[j] for j in range(len(vars_)) if j != i]
                if others:
                    clauses.append([-v] + others)

        return clauses

    # --- propagation with cache --------------------------------------------------

    def _board_state_key(self):
        """
        A hashable snapshot of the current board state.

        We capture both the drawn edges and the forbidden edges because two
        states can have the same drawn set but different forbidden sets
        (one might have had extra constraints applied already).
        """
        return (
            frozenset(self.board.all_drawn_edges),
            frozenset(self.board.unallowed_edges),
        )

    def propagate(self) -> bool:
        """
        Runs unit propagation: if a clause has only one unassigned literal,
        that literal is forced.  Repeat until stable or contradiction found.

        CACHE BEHAVIOUR
        ---------------
        Before running propagation, we check whether we have already processed
        this exact board state.  If yes, we replay the cached result directly
        onto the board — no clause iteration needed.

        If no cache hit, we run the full propagation and store the *delta*
        (only the newly-derived edges, not the ones that were already known)
        so that replaying is cheap.

        Returns True if stable (no contradiction), False if contradiction found.
        Writes forced assignments back to the board either way.
        """
        cache_key = self._board_state_key()

        # ---- cache hit ----------------------------------------------------------
        if cache_key in SATSolver._propagation_cache:
            valid, new_mandatory, new_forbidden = SATSolver._propagation_cache[cache_key]
            if valid:
                self._replay_cached_result(new_mandatory, new_forbidden)
            return valid

        # ---- cache miss: run the real propagation -------------------------------
        # Remember what we knew BEFORE propagation so we can store only the delta.
        known_drawn_before    = frozenset(self.board.all_drawn_edges)
        known_forbidden_before = frozenset(self.board.unallowed_edges)

        valid = self._run_unit_propagation()

        if valid:
            self._apply_to_board()

        # Compute the delta (what propagation newly discovered).
        new_mandatory = frozenset(self.board.all_drawn_edges) - known_drawn_before
        new_forbidden = frozenset(self.board.unallowed_edges) - known_forbidden_before

        SATSolver._propagation_cache[cache_key] = (valid, new_mandatory, new_forbidden)

        return valid

    def _replay_cached_result(self, new_mandatory: frozenset, new_forbidden: frozenset):
        """
        Applies a previously-computed propagation delta to the board without
        re-running any clause logic.
        """
        board = self.board
        for edge in new_mandatory:
            if edge not in board.all_drawn_edges:
                board.mandatory_drawn_edges.add(edge)
        for edge in new_forbidden:
            if edge in board.allowed_edges:
                board.allowed_edges.discard(edge)
                board.unallowed_edges.add(edge)

    def _run_unit_propagation(self) -> bool:
        """
        Core unit-propagation loop (extracted from the old `propagate` so the
        cache wrapper above can call it cleanly).

        Returns True if no contradiction was found, False otherwise.
        Does NOT write results to the board — that is done by the caller.
        """
        changed = True
        while changed:
            changed = False

            for clause in self.clauses:
                status, unassigned = self._evaluate_clause(clause)

                if status == 'satisfied':
                    continue

                if status == 'contradiction':
                    return False

                if status == 'unit':
                    lit = unassigned[0]
                    var = abs(lit)
                    value = lit > 0

                    if self.assignment[var] is not None:
                        if self.assignment[var] != value:
                            return False
                    else:
                        self.assignment[var] = value
                        changed = True

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