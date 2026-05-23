class SATSolver:
    """
    SAT solver otimizado para Slitherlink.
    Só gera constraints locais e faz propagação incremental.
    """

    def __init__(self, board):
        self.board = board

        self.edge_to_var = {e: i+1 for i, e in enumerate(board.all_edges)}
        self.var_to_edge = {v: e for e, v in self.edge_to_var.items()}

        self.assignment = {v: None for v in self.var_to_edge}
        self._load_board_state()

    # ------------------------------------------------------------

    def _load_board_state(self):
        for e in self.board.all_drawn_edges:
            if e in self.edge_to_var:
                self.assignment[self.edge_to_var[e]] = True

        for e in self.board.unallowed_edges:
            if e in self.edge_to_var:
                self.assignment[self.edge_to_var[e]] = False

    # ------------------------------------------------------------

    def propagate(self):

        changed = True

        while changed:
            changed = False

            # células
            for r in range(self.board.rows):
                for c in range(self.board.cols):

                    hint = self.board.board[r][c]
                    if hint == -1:
                        continue

                    res = self._propagate_cell(r, c, hint)
                    if res is False:
                        return False
                    changed |= res

            # vértices
            vertices = set()
            for e in self.board.all_drawn_edges:
                vertices.update(self._edge_vertices(e))

            for v in vertices:
                res = self._propagate_vertex(v)
                if res is False:
                    return False
                changed |= res

        self._apply()
        return True

    # ------------------------------------------------------------

    def _propagate_cell(self, r, c, hint):

        edges = self.board.get_cell_edges(r, c)

        drawn = []
        unknown = []

        for e in edges:
            val = self.assignment[self.edge_to_var[e]]
            if val is True:
                drawn.append(e)
            elif val is None:
                unknown.append(e)

        if len(drawn) > hint:
            return False

        if len(drawn) + len(unknown) < hint:
            return False

        changed = False

        # completar
        if len(drawn) == hint:
            for e in unknown:
                v = self.edge_to_var[e]
                if self.assignment[v] is None:
                    self.assignment[v] = False
                    changed = True

        # obrigar
        elif len(drawn) + len(unknown) == hint:
            for e in unknown:
                v = self.edge_to_var[e]
                if self.assignment[v] is None:
                    self.assignment[v] = True
                    changed = True

        return changed

    # ------------------------------------------------------------

    def _propagate_vertex(self, vertex):

        touching = self._edges_touching_vertex(vertex)

        drawn = []
        unknown = []

        for e in touching:
            v = self.edge_to_var[e]
            val = self.assignment[v]

            if val is True:
                drawn.append(e)
            elif val is None:
                unknown.append(e)

        deg = len(drawn)

        if deg > 2:
            return False

        changed = False

        # se já tem 2 → resto false
        if deg == 2:
            for e in unknown:
                v = self.edge_to_var[e]
                if self.assignment[v] is None:
                    self.assignment[v] = False
                    changed = True

        # se tem 1 e só falta 1 → tem de ligar
        elif deg == 1 and len(unknown) == 1:
            e = unknown[0]
            v = self.edge_to_var[e]
            if self.assignment[v] is None:
                self.assignment[v] = True
                changed = True

        # dead-end
        elif deg == 1 and len(unknown) == 0:
            return False

        return changed

    # ------------------------------------------------------------

    def _apply(self):

        board = self.board

        for var, val in self.assignment.items():

            if val is None:
                continue

            e = self.var_to_edge[var]

            if val:
                board.mandatory_drawn_edges.add(e)

            else:
                if e in board.allowed_edges:
                    board.allowed_edges.discard(e)
                    board.unallowed_edges.add(e)

    # ------------------------------------------------------------

    def _edge_vertices(self, edge):
        t, r, c = edge
        if t == 'h':
            return (r, c), (r, c+1)
        return (r, c), (r+1, c)

    def _edges_touching_vertex(self, vertex):
        vr, vc = vertex

        cand = [
            ('h', vr, vc),
            ('h', vr, vc-1),
            ('v', vr, vc),
            ('v', vr-1, vc)
        ]

        return [e for e in cand if e in self.board.all_edges]