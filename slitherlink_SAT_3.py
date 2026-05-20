# slitherlink_SAT_3.py - Versão otimizada do agente
#!/usr/bin/env python3

import random, copy
from sys import stdin
from collections import defaultdict
from functools import lru_cache

import utils
from utils import *

from search import (
    Problem,
    Node,
    astar_search,
    breadth_first_tree_search,
    depth_first_tree_search,
    greedy_search,
    recursive_best_first_search,
)

class SlitherlinkState:
    state_id = 0
    
    def __init__(self, board):
        self.board = board
        self.id = SlitherlinkState.state_id
        SlitherlinkState.state_id += 1
        self._hash_cache = None
    
    def __lt__(self, other):
        return self.id < other.id
    
    def get_board(self):
        return self.board
    
    def __eq__(self, other):
        if not isinstance(other, SlitherlinkState):
            return False
        return self.board.all_drawn_edges == other.board.all_drawn_edges
    
    def __hash__(self):
        if self._hash_cache is None:
            self._hash_cache = hash(frozenset(self.board.all_drawn_edges))
        return self._hash_cache

class Board:
    """Representação interna de um tabuleiro de Slitherlink - Versão otimizada."""
    
    def __init__(self, board: list):
        self.board = board
        self.rows = len(board)
        self.cols = len(board[0]) if self.rows > 0 else 0
        
        # Pré-calcular todas as edges
        self.all_edges = {
            ('h', r, c) for r in range(self.rows + 1) for c in range(self.cols)
        } | {
            ('v', r, c) for r in range(self.rows) for c in range(self.cols + 1)
        }
        
        self.allowed_edges = self.all_edges.copy()
        self.unallowed_edges = set()
        self.drawn_edges = set()
        self.mandatory_drawn_edges = set()
        self.contradiction = False
        
        # Cache para operações frequentes
        self._cell_edges_cache = {}
        self._adjacent_cells_cache = {}
        self._active_edges_cache = {}
        
        # Pré-calcular células adjacentes para cada edge
        self._edge_cells_cache = self._precompute_edge_cells()
    
    def _precompute_edge_cells(self):
        """Pré-calcula células afetadas por cada edge"""
        cache = {}
        for edge in self.all_edges:
            cells = self._compute_edge_cells(edge)
            cache[edge] = cells
        return cache
    
    def _compute_edge_cells(self, edge):
        """Computa células afetadas por uma edge"""
        t, r, c = edge
        cells = []
        if t == 'h':
            if r - 1 >= 0:
                cells.append((r - 1, c))
            if r < self.rows:
                cells.append((r, c))
        elif t == 'v':
            if c - 1 >= 0:
                cells.append((r, c - 1))
            if c < self.cols:
                cells.append((r, c))
        return cells
    
    def adjacent_cell(self, cell: tuple) -> list:
        """Retorna células adjacentes com cache"""
        if cell in self._adjacent_cells_cache:
            return self._adjacent_cells_cache[cell]
        
        a_cells = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_cell = (cell[0] + dr, cell[1] + dc)
            if 0 <= new_cell[0] < self.rows and 0 <= new_cell[1] < self.cols:
                a_cells.append(new_cell)
        
        self._adjacent_cells_cache[cell] = a_cells
        return a_cells
    
    def get_cell_edges(self, row: int, column: int) -> list:
        """Retorna edges da célula com cache"""
        key = (row, column)
        if key in self._cell_edges_cache:
            return self._cell_edges_cache[key]
        
        edges = [('h', row, column), ('h', row + 1, column),
                 ('v', row, column), ('v', row, column + 1)]
        self._cell_edges_cache[key] = edges
        return edges
    
    def get_active_edges(self, row: int, column: int) -> int:
        """Retorna número de edges ativas na célula"""
        count = 0
        edges = self.get_cell_edges(row, column)
        drawn = self.all_drawn_edges
        
        for edge in edges:
            if edge in drawn:
                count += 1
        return count
    
    def get_inactive_edges(self, row: int, column: int) -> int:
        """Retorna número de edges inativas"""
        return 4 - self.get_active_edges(row, column)
    
    @staticmethod
    def parse_instance():
        """Lê o tabuleiro do stdin"""
        layout = [[-1 if cell == '.' else int(cell) for cell in line.split()] 
                  for line in stdin]
        return Board(layout)
    
    @property
    def all_drawn_edges(self):
        return self.drawn_edges | self.mandatory_drawn_edges
    
    def get_board(self):
        return self.board
    
    def add_action(self, action):
        """Adiciona uma ação já verificada"""
        self.drawn_edges.add(action)
    
    def cells_adjacent_to_action(self, action):
        """Retorna células afetadas por uma edge (usando cache)"""
        return self._edge_cells_cache.get(action, [])
    
    def get_extremes(self):
        """Encontra pontas soltas de forma otimizada"""
        degree = defaultdict(int)
        
        for edge in self.all_drawn_edges:
            t, r, c = edge
            if t == 'h':
                v1, v2 = (r, c), (r, c + 1)
            else:
                v1, v2 = (r, c), (r + 1, c)
            degree[v1] += 1
            degree[v2] += 1
        
        extremes = []
        for edge in self.all_drawn_edges:
            t, r, c = edge
            if t == 'h':
                v1, v2 = (r, c), (r, c + 1)
            else:
                v1, v2 = (r, c), (r + 1, c)
            
            if degree[v1] == 1 or degree[v2] == 1:
                extremes.append(edge)
        
        return extremes
    
    def get_actions_from_extreme(self, extreme_edge, allowed_edges):
        """Retorna ações possíveis a partir de uma ponta"""
        t, r, c = extreme_edge
        candidates = []
        
        if t == 'h':
            candidates.extend([('h', r, c-1), ('v', r, c), ('v', r-1, c)])
            candidates.extend([('h', r, c+1), ('v', r, c+1), ('v', r-1, c+1)])
        else:
            candidates.extend([('v', r-1, c), ('h', r, c), ('h', r, c-1)])
            candidates.extend([('v', r+1, c), ('h', r+1, c), ('h', r+1, c-1)])
        
        result = []
        for action in candidates:
            if action in allowed_edges and action not in self.all_drawn_edges:
                result.append(action)
        
        return result
    
    def is_action_adjacent_to_edge(self, action):
        """Verifica se ação é adjacente a uma edge existente"""
        t, r, c = action
        drawn = self.all_drawn_edges
        
        if t == 'h':
            vertices = [(r, c), (r, c + 1)]
        else:
            vertices = [(r, c), (r + 1, c)]
        
        for edge in drawn:
            if edge[0] == 'h':
                ev1, ev2 = (edge[1], edge[2]), (edge[1], edge[2] + 1)
            else:
                ev1, ev2 = (edge[1], edge[2]), (edge[1] + 1, edge[2])
            
            if vertices[0] in (ev1, ev2) or vertices[1] in (ev1, ev2):
                return True
        
        return False
    
    def is_action_possible(self, action):
        """Verifica se ação não viola constraints das células"""
        cells_list = self.cells_adjacent_to_action(action)
        
        for cell in cells_list:
            cell_r, cell_c = cell
            cell_value = self.board[cell_r][cell_c]
            if cell_value == -1:
                continue
            
            n_active = self.get_active_edges(cell_r, cell_c)
            if n_active >= cell_value:
                return False
        
        return True
    
    def print(self) -> str:
        """Retorna representação do tabuleiro"""
        output_rows = []
        
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                top = '1' if ('h', r, c) in self.drawn_edges else '0'
                right = '1' if ('v', r, c + 1) in self.drawn_edges else '0'
                bottom = '1' if ('h', r + 1, c) in self.drawn_edges else '0'
                left = '1' if ('v', r, c) in self.drawn_edges else '0'
                
                cell_repr = top + right + bottom + left
                row_cells.append(cell_repr)
            
            output_rows.append("\t".join(row_cells))
        
        return "\n".join(output_rows)
    
    def print_complete(self) -> str:
        """Representação visual para debug"""
        output = []
        
        for r in range(self.rows):
            # Linha horizontal superior
            h_line = ""
            for c in range(self.cols):
                h_line += "+"
                if ('h', r, c) in self.all_drawn_edges:
                    h_line += "---"
                elif ('h', r, c) in self.unallowed_edges:
                    h_line += " x "
                else:
                    h_line += "   "
            h_line += "+"
            output.append(h_line)
            
            # Linha vertical e valores
            v_line = ""
            for c in range(self.cols):
                if ('v', r, c) in self.all_drawn_edges:
                    v_line += "|"
                elif ('v', r, c) in self.unallowed_edges:
                    v_line += "x"
                else:
                    v_line += " "
                
                val = str(self.board[r][c])
                v_line += f" {val if val != '-1' else ' '} "
            
            if ('v', r, self.cols) in self.all_drawn_edges:
                v_line += "|"
            elif ('v', r, self.cols) in self.unallowed_edges:
                v_line += "x"
            else:
                v_line += " "
            output.append(v_line)
        
        # Linha horizontal final
        last_h_line = ""
        for c in range(self.cols):
            last_h_line += "+"
            if ('h', self.rows, c) in self.all_drawn_edges:
                last_h_line += "---"
            elif ('h', self.rows, c) in self.unallowed_edges:
                last_h_line += " x "
            else:
                last_h_line += "   "
        last_h_line += "+"
        output.append(last_h_line)
        
        return "\n".join(output)

class Slitherlink(Problem):
    def __init__(self, board: Board, gui=None):
        """Construtor com propagação inicial otimizada"""
        self.gui = gui
        
        from SATOracle_3 import SATSolver
        from constraint_propagator import InitialPropagator
        
        temp_state = SlitherlinkState(board)
        
        propagator = InitialPropagator(temp_state)
        forbidden = propagator.unallowed_edges()
        mandatory = propagator.mandatory_edges()
        
        sat = SATSolver(board)
        sat.propagate()
        
        board.unallowed_edges = board.allowed_edges - (board.allowed_edges - set(forbidden))
        board.allowed_edges = board.allowed_edges - set(forbidden)
        board.mandatory_drawn_edges = mandatory
        
        self._actions_cache = {}
        
        initial_state = SlitherlinkState(board)
        self.initial = initial_state
    
    def actions(self, state: SlitherlinkState):
        """Retorna ações possíveis - versão otimizada com MRV"""
        board = state.board
        
        state_key = frozenset(board.all_drawn_edges)
        if state_key in self._actions_cache:
            return self._actions_cache[state_key]
        
        if getattr(board, 'contradiction', False):
            return ()
        
        drawn = board.all_drawn_edges
        
        if len(drawn) > 0:
            extremes = board.get_extremes()
            
            if extremes:
                best_feasible = []
                min_options = 999
                
                for extreme in extremes:
                    continuations = board.get_actions_from_extreme(extreme, board.allowed_edges)
                    feasible = [a for a in continuations if board.is_action_possible(a)]
                    
                    if len(feasible) == 0:
                        self._actions_cache[state_key] = ()
                        return ()
                    
                    if len(feasible) < min_options:
                        min_options = len(feasible)
                        best_feasible = feasible
                
                result = tuple(best_feasible)
                self._actions_cache[state_key] = result
                return result
        
        actions = board.allowed_edges - drawn
        
        if len(drawn) != 0:
            adjacent_actions = [a for a in actions if board.is_action_adjacent_to_edge(a)]
        else:
            adjacent_actions = list(actions)
        
        feasible_actions = [a for a in adjacent_actions if board.is_action_possible(a)]
        result = tuple(feasible_actions)
        self._actions_cache[state_key] = result
        return result
    
    def result(self, state, action):
        """Transição de estado com propagação SAT"""
        from SATOracle_3 import SATSolver
        
        board = state.get_board()
        newBoard = copy.deepcopy(board)
        
        if isinstance(action, tuple) and isinstance(action[0], str):
            newBoard.add_action(action)
        else:
            for act in action:
                newBoard.add_action(act)
        
        sat = SATSolver(newBoard)
        valid = sat.propagate(use_cache=True)
        
        if not valid:
            newBoard.contradiction = True
        
        return SlitherlinkState(newBoard)
    
    def goal_test(self, state: SlitherlinkState):
        """Teste de objetivo completo"""
        board = state.get_board()
        drawn_edges = board.all_drawn_edges
        
        if len(drawn_edges) == 0:
            return False
        
        # Verificar dicas
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint != -1:
                    if board.get_active_edges(r, c) != hint:
                        return False
        
        # Verificar grau dos vértices
        degree = {}
        for edge in drawn_edges:
            t, r, c = edge
            if t == 'h':
                v1, v2 = (r, c), (r, c + 1)
            else:
                v1, v2 = (r, c), (r + 1, c)
            degree[v1] = degree.get(v1, 0) + 1
            degree[v2] = degree.get(v2, 0) + 1
        
        for v, deg in degree.items():
            if deg != 2:
                return False
        
        # Verificar conectividade (um único loop)
        if drawn_edges:
            # Encontrar um vértice com grau 2
            start_vertex = None
            for v, deg in degree.items():
                if deg == 2:
                    start_vertex = v
                    break
            
            if start_vertex is None:
                return False
            
            visited = set()
            queue = [start_vertex]
            visited.add(start_vertex)
            
            while queue:
                current = queue.pop(0)
                for edge in drawn_edges:
                    t, r, c = edge
                    if t == 'h':
                        v1, v2 = (r, c), (r, c + 1)
                    else:
                        v1, v2 = (r, c), (r + 1, c)
                    
                    if current == v1 or current == v2:
                        other = v2 if current == v1 else v1
                        if other not in visited:
                            visited.add(other)
                            queue.append(other)
            
            vertices_with_deg2 = {v for v, deg in degree.items() if deg == 2}
            if visited != vertices_with_deg2:
                return False
        
        return True
    
    def h(self, node: Node):
        """Heurística para A* e Greedy"""
        board = node.state.get_board()
        
        cell_active = defaultdict(int)
        for edge in board.all_drawn_edges:
            t, r, c = edge
            if t == 'h':
                if r < board.rows:
                    cell_active[(r, c)] += 1
                if r - 1 >= 0:
                    cell_active[(r-1, c)] += 1
            else:
                if c < board.cols:
                    cell_active[(r, c)] += 1
                if c - 1 >= 0:
                    cell_active[(r, c-1)] += 1
        
        score = 0.0
        
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue
                
                active = cell_active.get((r, c), 0)
                missing = hint - active
                
                if missing == 0:
                    score -= 8.0
                elif missing > 0:
                    score += missing * 5.0
                else:
                    score += 200.0
        
        # Penalizar pontas soltas
        degree = defaultdict(int)
        for edge in board.all_drawn_edges:
            t, r, c = edge
            if t == 'h':
                v1, v2 = (r, c), (r, c + 1)
            else:
                v1, v2 = (r, c), (r + 1, c)
            degree[v1] += 1
            degree[v2] += 1
        
        loose_ends = sum(1 for deg in degree.values() if deg == 1)
        score += loose_ends * 12.0
        
        return score