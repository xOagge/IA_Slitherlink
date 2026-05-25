#!/usr/bin/python3
# slitherlink.py: Template para implementação do projeto de Inteligência Artificial 2025/2026.
# Devem alterar as classes e funções neste ficheiro de acordo com as instruções do enunciado.
# Além das funções e classes sugeridas, podem acrescentar outras que considerem pertinentes.

# Grupo 00:
# 00000 Nome1
# 00000 Nome2

import random, copy
from sys import stdin
from collections import defaultdict

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
        self.board:Board = board
        self.id = SlitherlinkState.state_id
        SlitherlinkState.state_id += 1

        #tem as actions permitidas, pois corre-se o propagator antes
        self.allowed_actions = ()
    
    def __lt__(self, other):
        return self.id < other.id

    # TODO: outros metodos da classe

    def get_board(self):
        return self.board
    
    def __eq__(self, other):
        if not isinstance(other, SlitherlinkState):
            return False
            
        # 1. Faz a comparação matemática
        is_equal = self.board.all_drawn_edges == other.board.all_drawn_edges
        
        # 2. Se forem de facto iguais, avisa no terminal!
        if is_equal:
            print(f"⚠️ CORTE DFS: Tabuleiro repetido detetado! (Arestas: {len(self.board.drawn_edges)}) - Ramo cortado.")
            
        return is_equal

    def __hash__(self):
        # Muito mais leve e rápido de calcular
        return hash(frozenset(self.board.all_drawn_edges))

class Board:
    """Representação interna de um tabuleiro de Slitherlink."""

    def adjacent_cell(self, cell:tuple) -> list:
        """Devolve uma lista das células que fazem
        fronteira com a célula enviada no argumento"""

        #lista de celulas adjacentes
        a_cells = []

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_cell = (cell[0] + dr, cell[1] + dc)
            #checkl if calculated cell is inside board
            #cell is treated as having indexes
            if 0 <= new_cell[0] < self.rows and \
               0 <= new_cell[1] < self.cols:
                a_cells.append(new_cell)

        return a_cells

    def get_cell_edges(self, row:int, column:int) -> list:
        """Devolve os arestas da célula enviada no argumento"""

        #cada celula segue esta logica, nao existe celulas com regimes
        #de arestas diferente como no caso de adjacent_cells
        return [('h',row, column), ('h',row+1, column), \
                ('v',row, column), ('v',row, column+1)]

    #exemplo retorna numero, o template diz -> list, alterei para ->int
    def get_active_edges(self, row:int, column:int) -> int:
        """Devolve o número de arestas ativas"""
        count = 0
        for edge in self.all_drawn_edges:
            if edge == ('h',row, column) or edge == ('h',row+1, column) \
               or edge == ('v',row, column) or edge == ('v',row, column+1):
               count += 1
        return count

    @staticmethod
    def parse_instance():
        """Lê o test do standard input (stdin) que é passado como argumento
        e retorna uma instância da classe Board.

        Por exemplo:
            $ python3 pipe.py < test-01.txt

            > from sys import stdin
            > line = stdin.readline().split()
        """
        
        #layout = [line.split() for line in stdin]
        layout = [[-1 if cell == '.' else int(cell) for cell in line.split()] for line in stdin]
        return Board(layout)

        #exemplo retorna um numero
    
    def get_inactive_edges(self, row:int, column:int) -> int:
        """Devolve o número de arestas ativas"""
        count = 4
        for edge in self.all_drawn_edges:
            if edge == ('h',row, column) or edge == ('h',row+1, column) \
               or edge == ('v',row, column) or edge == ('v',row, column+1):
               count -= 1
        return count

    # TODO: outros metodos da classe ----------------------------------

    def __init__(self, board:list):
        self.board:list = board
        self.rows:int = len(board) #row size
        self.cols:int = len(board[0]) #column size

        #sendo uma board NxM comprimento, temos 
        # N+1 rows e M columns de linhas horizontais 
        # N rows e M+1 columns de linhas verticais
        #range(X)-> [0,X-1], entao para ter K elementos, range(K)

        #TODAS AS EDGES PARA A BOARD DEFINIDA -----------------
        self.all_edges = {
            ('h', r, c) for r in range(self.rows + 1) for c in range(self.cols)
        } | {
            ('v', r, c) for r in range(self.rows) for c in range(self.cols + 1)
        }

        
        #GLOBAL EDGES
        self.global_forbidden = set() #globally forbidden
        self.global_drawn = set() #globally mandatory
        self.global_domain = set() #globally all edges we can interact with

        #STATE LEVEL RULES
        self.forbidden_edges = set() #state forbidden
        self.drawn_edges = set() #state drawn

        #RECENTLY UPDATED EDGES
        self.recently_changed_edges = set()

    @property
    def all_drawn_edges(self):
        """ALL STATE DRAWN EDGES"""
        return self.drawn_edges | self.global_drawn
    
    @property
    def all_forbidden_edges(self):
        """ALL STATE FORBIDDEN EDGES"""
        return self.forbidden_edges | self.global_forbidden


    def draw_edge(self, action):
        self.drawn_edges.add(action)
        self.recently_changed_edges.add(action)

    def draw_edges(self, action):
        self.drawn_edges.update(action)
        self.recently_changed_edges.update(action)
    
    def forbid_edge(self, action):
        self.forbidden_edges.add(action)
        self.recently_changed_edges.add(action)
    
    def forbid_edges(self, action):
        self.forbidden_edges.update(action)
        self.recently_changed_edges.update(action)


    #CALCULAR CONECTIVIDADE DAS EDGES ------------------

    def get_edge_vertices(self, edge):
        t, r, c = edge
        vertices = ()
        if t == 'h': vertices = ((r, c), (r, c + 1))
        else: vertices = ((r, c), (r + 1, c))
        return vertices

    def get_edges_connectivity(self):
        """Importancia: 
            -vertice com conectividade 2: restantes
        edges sao proibidas
            -vertice conectividade 1: loose edge, podemos fazer
        proxima acao aqui
            -vertice conectividade 0: no meio do nada, nao vamos
            construir aqui
        return : {edge: (v1 connect, v2 connect)}
        """
        #{vertice: numero de vezes tocado}
        vertice_count = defaultdict(int)
        #iterate edges
        for edge in self.all_drawn_edges:
            vertices = self.get_edge_vertices(edge)
            vertice_count[vertices[0]] += 1
            vertice_count[vertices[1]] += 1

        #{edge: (v1 connect, v2 connect)}
        connectivity = {}
        for edge in self.all_edges:
            v1, v2 = self.get_edge_vertices(edge)
            # O grau é 0 se o vértice não estiver no dicionário
            connectivity[edge] = ((v1,vertice_count.get(v1, 0)), (v2,vertice_count.get(v2, 0)))
        
        return connectivity
    
    def get_edges_around_vertex(self, vertex):
        """para em ConstraintPropagator sabermos que edges estao desenhadas, proibidas,
        etc, a volta de um vertice, usamos este metodo. da return a todas as relevantes
        , proibidas, e desenhadas, para em constraintPropagator poder receber a situacao
        local na sua totalidade"""
        r, c = vertex[0], vertex[1]
        relevant_edges = {('h', r, c-1),('h', r, c),('v', r-1, c),('v', r, c)}
        relevant_edges = {e for e in relevant_edges if e in self.all_edges}

        #relevantes desenhadas
        drawn = relevant_edges.intersection(self.all_drawn_edges)

        #relevantes proibidas
        prohibited = relevant_edges.intersection(self.all_forbidden_edges)

        undrawn = relevant_edges - drawn - prohibited

        return (prohibited, drawn, undrawn)
        
        
    #METODOS PARA INTERAGIRA COES COM CELULAS
        
    def is_action_adjacent_to_edge(self, action):
        """metodo criado para verificar se acao vai criar uma edge
        conectada a uma outra, crucial para afunilar a arvora para solucoes
        plausiveis mais rapido, da return a true ou false, meaning que a
        edge action e conectada ou nao"""

        #orgulhoso de ter feito com desenhinhos, usei o gemini pro para confirmar
        # se logica fazia sentido (mas o clanker nao verificou um erro de que uma
        #last action fecha um ciclo com count 2, otario)

        #util para saber se edge nao cria um branch, nao aceitavel como solucao
        count_1 = 0
        count_2 = 0

        t, r, c = action #type, row, col
        if t == 'h':
            for edge in self.all_drawn_edges:
                t2, r2, c2 = edge
                if t2 == 'h':
                    if r == r2 and c-1 == c2: count_1 += 1
                    if r == r2 and c+1 == c2: count_2 += 1
                if t2 == 'v':
                    if r-1 == r2 and c == c2 or r == r2 and c == c2:
                        count_1 += 1
                    if r-1 == r2 and c+1 == c2 or r == r2 and c+1 == c2:
                        count_2 += 1
        elif t == 'v':
            for edge in self.all_drawn_edges:
                t2, r2, c2 = edge
                if t2 == 'h':
                    if r == r2 and c-1 == c2 or r == r2 and c == c2:
                        count_1 += 1
                    if r+1 == r2 and c == c2 or r+1 == r2 and c-1 == c2:
                        count_2 += 1
                if t2 == 'v':
                    if r-1 == r2 and c == c2:
                        count_1 += 1
                    if r+1 == r2 and c == c2:
                        count_2 += 1
        # nenhum vertice tem branch, e esta conectado em pelo menos um dos lados
        if count_1 <= 1 and count_2 <= 1 and count_1 + count_2 >= 1: 
            return True
        return False

    def cells_adjacent_to_edge(self, action):
        """metodo criado para encontra cells adjacented? afetadas
        pela criacao de uma linha, vai ser usado para avaliar se esta
        nova linha vai levar a uma celula exceder o valor limite proprio"""
        t, r, c = action #type, row, col
        #encontrar celulas adjacentes a linha correspondente a action
        cells_list = []
        if t == 'h':
            if r-1 >= 0: cells_list.append((r-1, c))
            if r < self.rows: cells_list.append((r, c))
        elif t == 'v':
            if c-1 >= 0: cells_list.append((r, c-1))
            if c < self.cols: cells_list.append((r, c))
        return cells_list
    
    def is_action_possible(self, action):
        cells_list = self.cells_adjacent_to_edge(action)

        #para as celulas afetadas, vamos ver se ja nao teem linhas limite
        for cell in cells_list:
            cell_r, cell_c = cell[0], cell[1]
            cell_value = self.board[cell_r][cell_c] #valor na celula
            if cell_value == "." or cell_value == -1: continue #celuluas com '.' podem tudo
            n_active_edges = self.get_active_edges(cell_r, cell_c) #n linhas ja ativas
            #se n linhas ativas e igual ao maximo que a celula pode ter, marcar acao
            #como inplausivel
            if n_active_edges >= int(cell_value):
                return False
        #se foi verificado para todas as celulas afetadas por esta acao que nao estao
        #ja no seu limite, podemos entao considerar esta acao plausivel
        return True

    #METODO DE COPY

    #AIAIAIAIAIAAIAIAIAIIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIAIA
    def new_state(self):
        """
        Deep copy do Board para evitar partilha de estado entre nós da procura.
        """

        # 1. Nova board com o mesmo layout base
        novo_tabuleiro = Board(self.board)

        # 2. Copiar GLOBALS (normalmente são partilhados logicamente,
        # mas se queres total isolamento na search tree, copia tudo)
        novo_tabuleiro.global_forbidden = self.global_forbidden.copy()
        novo_tabuleiro.global_drawn = self.global_drawn.copy()
        novo_tabuleiro.global_domain = self.global_domain.copy()

        # 3. Copiar STATE (isto é o que muda durante a procura)
        novo_tabuleiro.forbidden_edges = self.forbidden_edges.copy()
        novo_tabuleiro.drawn_edges = self.drawn_edges.copy()

        # 4. Want to reset recent actions, as its used for the state applied actions
        novo_tabuleiro.recently_changed_edges = set()

        return novo_tabuleiro

    #AIAIAIAIAIAIAIAIIAIAIAIAIAIAIAIAIIAIA
    def print(self) -> str:
        output_lines = []
        
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):

                top    = "1" if ('h', r, c) in self.drawn_edges else "0"
                right  = "1" if ('v', r, c+1) in self.drawn_edges else "0"
                bottom = "1" if ('h', r+1, c) in self.drawn_edges else "0"
                left   = "1" if ('v', r, c) in self.drawn_edges else "0"

                row_cells.append(f"{top}{right}{bottom}{left}")

            output_lines.append("\t".join(row_cells))

        return "\n".join(output_lines)

    #FULL GEMINI - usado durante o desenvolvimento para visualizar como
    #o algoritmo se propaga e refletir sobre que dificuldades tem
    def print_complete(self) -> str:
            """
            Retorna uma representação visual do tabuleiro para debugging.
            + x +   +-------+
            x   |   |       |
            +---+   2       x

            As arestas desenhadas usam '---' e '|'.
            As arestas proibidas usam ' x ' e 'x'.
            """
            output = []
            
            # Fallback seguro caso a variável forbidden_edges ainda não exista no board
            unallowed = getattr(self, 'forbidden_edges', set())
            
            for r in range(self.rows):
                # 1. Linha das arestas HORIZONTAIS e Vértices
                h_line = ""
                for c in range(self.cols):
                    h_line += "+"
                    if ('h', r, c) in self.all_drawn_edges:
                        h_line += "---"
                    elif ('h', r, c) in self.all_forbidden_edges:
                        h_line += " x "  # Representação visual da proibição horizontal
                    else:
                        h_line += "   "
                h_line += "+" # Último vértice da linha
                output.append(h_line)

                # 2. Linha das arestas VERTICAIS e Valores das Células
                v_line = ""
                for c in range(self.cols):
                    if ('v', r, c) in self.all_drawn_edges:
                        v_line += "|"
                    elif ('v', r, c) in self.all_forbidden_edges:
                        v_line += "x"    # Representação visual da proibição vertical
                    else:
                        v_line += " "
                    
                    # Converter para string, mas imprimir espaço se for '-1'
                    val = str(self.board[r][c])
                    v_line += f" {val if val != '-1' else ' '} "
                
                # Última aresta vertical da linha
                if ('v', r, self.cols) in self.all_drawn_edges:
                    v_line += "|"
                elif ('v', r, self.cols) in self.all_forbidden_edges:
                    v_line += "x"
                else:
                    v_line += " "
                output.append(v_line)

            # 3. Linha HORIZONTAL final (fundo do tabuleiro)
            last_h_line = ""
            for c in range(self.cols):
                last_h_line += "+"
                if ('h', self.rows, c) in self.all_drawn_edges:
                    last_h_line += "---"
                elif ('h', self.rows, c) in self.all_forbidden_edges:
                    last_h_line += " x "
                else:
                    last_h_line += "   "
            last_h_line += "+"
            output.append(last_h_line)
            output.append('\n-----------------------------------\n')

            return "\n".join(output)   
    
class Slitherlink(Problem):
    def __init__(self, board: Board, gui=None):
        """O construtor especifica o estado inicial."""

        #local import para nao criar circularidade de imports
        from initial_propagator import InitialPropagator
        from SATOracle import ConstraintPropagator

        self.gui = gui
        
        #CALCULAR GLOBAL FORBIDDEN E MANDATORY EDGES
        Board = board.new_state()
        
        temp_state = SlitherlinkState(Board)
        init_propagator = InitialPropagator(temp_state)

        forbidden = init_propagator.forbidden_edges()
        mandatory = init_propagator.mandatory_edges()

        #INJETAR GLOBAIS EM BOARD
        Board.global_forbidden = Board.all_edges.intersection(set(forbidden))
        Board.global_drawn = Board.all_edges.intersection(set(mandatory))
        Board.global_domain = Board.all_edges - Board.global_forbidden
        Board.recently_changed_edges = Board.global_drawn | Board.global_forbidden

        # print("--- Board after Initial Constraints (Before Cascade Propagation) ---")
        # print(Board.print_complete())

        # Correr o Motor de Dedução (Efeito Cascata)
        propagator = ConstraintPropagator(Board)
        allowed_actions = propagator.propagate()

        # Criar o estado inicial verdadeiro PARA A PROCURA
        initial_state = SlitherlinkState(Board)
        
        if allowed_actions is False:
            initial_state.is_valid = False
            initial_state.allowed_actions = []
        else:
            initial_state.is_valid = True
            initial_state.allowed_actions = allowed_actions
            
        self.initial = initial_state
        self.visited_hashes = set()

        #mostra InitialPropagator + ConstraintPropagator
        # print("--- Board after InitialPropagator + ConstraintPropagator ---")
        # print(self.initial.board.print_complete())

    #AIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIIA
    def rank_actions(self, state: SlitherlinkState, actions: list) -> list:
        """
        Orders actions from most promising to least promising to optimize DFS branching.
        Does not alter legality; only provides a heuristic sorting.
        """
        board = state.board
        drawn = board.all_drawn_edges

        # 1) GET ALL VERTICES DEGREES
        vertex_degrees = {}
        for edge in drawn:
            v1, v2 = board.get_edge_vertices(edge)
            if v1 in vertex_degrees: vertex_degrees[v1] = vertex_degrees[v1] + 1
            else: vertex_degrees[v1] = 1

            if v2 in vertex_degrees: vertex_degrees[v2] = vertex_degrees[v2] + 1
            else: vertex_degrees[v2] = 1

        def score_action(action):            
            score = 0
            v1, v2 = board.get_edge_vertices(action)
            d1 = vertex_degrees.get(v1, 0)
            d2 = vertex_degrees.get(v2, 0)

            # 1) PRIORIZAR FECHAR LOOPS, EXTENDER EXTREMOS, 
            # PENALIZA FRAGMENTACAO (da forma como temos o codigo apenas devem ser candidatos
            # acoes em loose edges, mas caso tenhamos um erro)
            
            #se os dois vertices ja teem degree 1, vai fechar um loop
            if d1 == 1 and d2 == 1:
                score += 100
            #else, se um dos vertices for degree 1, vai extender loose edge
            elif d1 == 1 or d2 == 1:
                # Extends an existing loose end.
                score += 50
            #else, se degree e 0 nos dois vertices, estamos a desenhar no nada
            elif d1 == 0 and d2 == 0:
                score -= 20


            # 2)
            
            adj_cells = board.cells_adjacent_to_edge(action)
            for r, c in adj_cells:
                hint = board.board[r][c]
                if hint != -1 and hint != ".":
                    hint_val = int(hint)
                    active = board.get_active_edges(r, c)
                    missing_needed = hint_val - active

                    # If the cell only needs ONE more edge to be satisfied, drawing this
                    # edge will trigger your propagator to lock down the rest of the cell.
                    if missing_needed == 1:
                        score += 30
                    
                    # Inherently favor larger numbers as they anchor the board
                    if hint_val == 3:
                        score += 15
                    elif hint_val == 2:
                        score += 5

            return score

        # 2. Sort actions descending based on their heuristic score
        return sorted(actions, key=score_action, reverse=True)

    #AIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIIA
    def actions(self, state: SlitherlinkState):
        #print(f"Pedindo actions para tabuleiro com {len(state.board.drawn_edges)} arestas. Hash: {hash(state)}")
        if getattr(state, 'is_valid', True) is False:
            return []

        board = state.board
        drawn = board.all_drawn_edges

        # ----------------------------------------------------------------
        # FIRST MOVE: no edges drawn yet.
        # Start at the most constrained cell (highest hint) to anchor the
        # search immediately instead of trying all 200+ edges on the board.
        # ----------------------------------------------------------------
        if not drawn:
            for num in [3, 2, 1]:
                for r in range(board.rows):
                    for c in range(board.cols):
                        if board.board[r][c] == num:
                            edges = board.get_cell_edges(r, c)
                            # Filter: edge must be allowed AND not violate cell limits
                            valid = [e for e in edges
                                    if e in board.global_domain
                                    and board.is_action_possible(e)]
                            if valid:
                                return valid
            # Fallback: no hints at all (unusual), return any allowed edge
            return [next(iter(board.global_domain))] if board.global_domain else []

        # ----------------------------------------------------------------
        # MID-SEARCH: find all loose-end vertices (degree == 1).
        # There should always be exactly 2 while the path is open.
        # ----------------------------------------------------------------
        # Count degree of every vertex touched by drawn edges
        degree = defaultdict(int)
        for edge in drawn:
            v1, v2 = board.get_edge_vertices(edge)
            degree[v1] += 1
            degree[v2] += 1

        loose_ends = [v for v, d in degree.items() if d == 1]

        # No loose ends: the loop is closed. goal_test will handle it.
        if not loose_ends:
            return []

        # ----------------------------------------------------------------
        # MRV: for each loose end, compute valid continuations.
        # Return the options of the MOST CONSTRAINED end (fewest choices).
        # If any end has 0 options → dead end → prune immediately.
        # ----------------------------------------------------------------
        best_options = None

        for vertex in loose_ends:
            _, _, undrawn = board.get_edges_around_vertex(vertex)
            # An edge is valid if it's still allowed and doesn't break cell limits
            options = [e for e in undrawn
                    if e in board.global_domain
                    and board.is_action_possible(e)]

            # Dead end: this loose end has nowhere to go
            if len(options) == 0:
                return []

            # MRV: keep the vertex with fewest options
            if best_options is None or len(options) < len(best_options):
                best_options = options

            valid_actions = list(best_options)
            if not valid_actions:
                return []

        return self.rank_actions(state, valid_actions)

    def result(self, state, action):
        """adiciona uma action que foi selecionada em actions, e faz a
        constrains propagation"""

        from SATOracle import ConstraintPropagator

        # 1 --- CRIAR NOVA BOARD, APLICAR ACTION, E PROPAGAR CONSTRAINTS

        new_board = state.board.new_state()  #copy board
        #draw action/actions
        if isinstance(action, tuple) and isinstance(action[0], str):
            new_board.draw_edge(action)
        else:
            for act in action:
                new_board.draw_edge(act)
        #propagate on new board, and check if valid (propagate altera a new_board em si)
        propagator = ConstraintPropagator(new_board)
        is_valid = propagator.propagate()
        new_state = SlitherlinkState(new_board) #define new state

        #print(new_state.board.print_complete())

        # 2 --- VERIFICAR SE NOVA BOARD E VALIDA

        # 2.1 --- SE PROPAGATE RESUMIU INVALIDO, NOVA BOARD E INVALIDA
        if is_valid is False:
            new_state.is_valid = False
            return new_state
        
        
        # 2.2 --- SE FECHOU UM LOOP, E É LOOP PREMATURO, NOVA BOARD E INVALIDA
        if self._has_premature_loop(new_state):
            new_state.is_valid = False
            return new_state
        
        # 3 --- SE TEM CELULAS UNREACHABLE E NAO CORRESPONDIDAS, BOARD E INVALIDA
        if self.is_region_unreachable(new_state):
            new_state.is_valid = False
            return new_state

        # 4 --- SE PASSOU POR FILTROS, ENTAO A NOVA BOARD E VALIDA 
        new_state.is_valid = True
        new_state.allowed_actions = is_valid
            
        return new_state
    
    # LOOP FUNCTIONS
    def check_if_closes_somewhere(self, state1: SlitherlinkState, state2: SlitherlinkState) -> bool:
        """
        comapra dois estados, um anterior e um posterior, para verificar se u loop foi criado
        atraves do numero de vertices com grau 1 apos adicoinar action e fazer propagation.
        """
        # propagator pode ter adicionado mais coisas, temos de comparar as duas boards
        added_edges = state2.board.all_drawn_edges - state1.board.all_drawn_edges
        
        # coords dos vertices afetados a adicionar linhas
        affected_vertices = set()
        for edge in added_edges:
            v1, v2 = state2.board.get_edge_vertices(edge)
            affected_vertices.add(v1)
            affected_vertices.add(v2)
            
        # Contar os vértices de grau 1 (pontas soltas) ANTES e DEPOIS, mas apenas nestes vértices
        old_v1_count = 0
        new_v1_count = 0
        
        for v in affected_vertices:
            # Grau na board antiga (state1)
            _, old_drawn, _ = state1.board.get_edges_around_vertex(v)
            if len(old_drawn) == 1:
                old_v1_count += 1
                
            # Grau na board nova (state2)
            _, new_drawn, _ = state2.board.get_edges_around_vertex(v)
            if len(new_drawn) == 1:
                new_v1_count += 1

        # O filtro: Se o número de pontas soltas locais diminuiu, as linhas chocaram!
        return new_v1_count < old_v1_count

    def _has_premature_loop(self, state: SlitherlinkState) -> bool:
        board = state.board
        drawn = board.all_drawn_edges
        if not drawn:
            return False

        from collections import defaultdict
        adj = defaultdict(list)
        for edge in drawn:
            t, r, c = edge
            v1 = (r, c)
            v2 = (r, c + 1) if t == 'h' else (r + 1, c)
            adj[v1].append(edge)
            adj[v2].append(edge)

        visited_edges = set()

        for start_edge in drawn:
            if start_edge in visited_edges:
                continue

            comp_edges = set()
            queue = [start_edge]
            comp_edges.add(start_edge)
            comp_vertices = set()

            while queue:
                curr = queue.pop(0)
                t, r, c = curr
                v1 = (r, c)
                v2 = (r, c + 1) if t == 'h' else (r + 1, c)
                comp_vertices.add(v1)
                comp_vertices.add(v2)

                for v in (v1, v2):
                    for neighbor_edge in adj[v]:
                        if neighbor_edge not in comp_edges:
                            comp_edges.add(neighbor_edge)
                            queue.append(neighbor_edge)

            visited_edges.update(comp_edges)

            is_closed = True
            for v in comp_vertices:
                if len(adj[v]) != 2:
                    is_closed = False
                    break

            if is_closed:
                if len(comp_edges) != len(drawn):
                    return True

                for r in range(board.rows):
                    for c in range(board.cols):
                        hint = board.board[r][c]
                        if hint != -1 and board.get_active_edges(r, c) != hint:
                            return True

        return False

    #AIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIIA
    def is_region_unreachable(self, state) -> bool:
        """
        Global topological pruning check.
        Returns True if any unsatisfied cell is structurally cut off from the
        current partial loop — meaning no candidate edge of that cell can ever
        be reached by extending the loop from its current loose ends.
        """
        board = state.board
        drawn = board.all_drawn_edges
        all_edges = board.all_edges
        unallowed = board.forbidden_edges

        # ------------------------------------------------------------------
        # 1. Find loose-end vertices (degree 1 in drawn edges).
        #    These are the only vertices from which the loop can grow.
        #    If there are no loose ends and the board is not solved, the loop
        #    is already closed — nothing more can be drawn.
        # ------------------------------------------------------------------
        degree = {}
        for edge in drawn:
            t, r, c = edge
            v1 = (r, c)
            v2 = (r, c + 1) if t == 'h' else (r + 1, c)
            degree[v1] = degree.get(v1, 0) + 1
            degree[v2] = degree.get(v2, 0) + 1

        loose_ends = [v for v, d in degree.items() if d == 1]

        # No loose ends → loop is closed (or empty). Nothing reachable.
        # An empty board has no drawn edges, so no loose ends either.
        # In both cases: if any cell is unsatisfied, it cannot be reached.
        # We only skip the check entirely if the board is already complete,
        # which goal_test handles separately. Here we just compute reachability.
        if not loose_ends:
            # If any unsatisfied hinted cell exists, it's unreachable.
            for r in range(board.rows):
                for c in range(board.cols):
                    hint = board.board[r][c]
                    if hint == -1:
                        continue
                    hint = int(hint)
                    if board.get_active_edges(r, c) < hint:
                        return True
            return False

        # ------------------------------------------------------------------
        # 2. BFS from all loose ends simultaneously through valid edges.
        #    "Valid" = in all_edges AND not in forbidden_edges.
        #    We traverse vertex-to-vertex through candidate edges.
        # ------------------------------------------------------------------
        reachable_vertices = set(loose_ends)
        queue = list(loose_ends)

        # Precompute: vertex → list of candidate edges (not unallowed)
        # We build this lazily during BFS to avoid scanning all edges upfront.
        def candidate_edges_at(vr, vc):
            """All valid (non-forbidden) edges touching vertex (vr, vc)."""
            possible = [
                ('h', vr, vc),
                ('h', vr, vc - 1),
                ('v', vr, vc),
                ('v', vr - 1, vc),
            ]
            return [e for e in possible if e in all_edges and e not in unallowed]

        while queue:
            vr, vc = queue.pop(0)
            for edge in candidate_edges_at(vr, vc):
                t, r, c = edge
                v1 = (r, c)
                v2 = (r, c + 1) if t == 'h' else (r + 1, c)
                for neighbor in (v1, v2):
                    if neighbor not in reachable_vertices:
                        reachable_vertices.add(neighbor)
                        queue.append(neighbor)

        # ------------------------------------------------------------------
        # 3. For each unsatisfied hinted cell, check if at least one of its
        #    candidate (non-forbidden, not yet drawn) edges touches a
        #    reachable vertex. If none do, the cell is cut off → prune.
        # ------------------------------------------------------------------
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue
                hint = int(hint)

                active = board.get_active_edges(r, c)
                if active >= hint:
                    continue  # already satisfied, skip

                # Check candidate edges: not drawn, not forbidden
                cell_edges = board.get_cell_edges(r, c)
                has_reachable = False
                for edge in cell_edges:
                    if edge in drawn or edge in unallowed:
                        continue  # already decided, doesn't count as reachable path
                    # This edge is still a candidate. Check if either of its
                    # vertices is reachable from the current loose ends.
                    t, er, ec = edge
                    v1 = (er, ec)
                    v2 = (er, ec + 1) if t == 'h' else (er + 1, ec)
                    if v1 in reachable_vertices or v2 in reachable_vertices:
                        has_reachable = True
                        break

                if not has_reachable:
                    return True  # this cell is cut off → prune this branch

        return False

    #AIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIIA
    def goal_test(self, state: SlitherlinkState):
        """
        Verifica se o estado atual é a solução final do puzzle.
        """
        board = state.board
        
        # CORREÇÃO 1: Usar all_drawn_edges
        if not board.all_drawn_edges:
            return False

        # --- TESTE 1: Regras dos Quadrados Numerados ---
        # (Assumindo que tens um dicionário de quadrados ou método equivalente na board)
        # Ajusta esta iteração de acordo com a forma como guardas as restrições iniciais.
        for r in range(board.rows):
            for c in range(board.cols):
                cell_value = board.board[r][c] # ou de onde lês o valor original
                if cell_value != "." and cell_value != -1:
                    n_active = board.get_active_edges(r, c)
                    # Se um único quadrado não estiver satisfeito, falhou o teste
                    if n_active != int(cell_value):
                        return False

        # --- Construir Lista de Adjacência para os próximos testes ---
        # CORREÇÃO 2: Usar all_drawn_edges
        adj = {}
        for edge in board.all_drawn_edges:
            v1, v2 = board.get_edge_vertices(edge)
            adj.setdefault(v1, []).append(v2)
            adj.setdefault(v2, []).append(v1)

        # --- TESTE 2: Continuidade Perfeita (Grau 2) ---
        for v, neighbors in adj.items():
            if len(neighbors) != 2:
                return False # Há uma ponta solta ou um cruzamento

        # --- TESTE 3: Único Ciclo Fechado (No premature/disjoint loops) ---
        # Fazemos uma travessia simples (BFS) a partir de um vértice qualquer
        # Se no final não visitámos todos os vértices da lista, existem ciclos separados!
        start_node = next(iter(adj))
        visited = set()
        queue = [start_node]
        
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        queue.append(neighbor)

        # Se visitámos menos vértices do que os que têm linhas, há fragmentos isolados
        if len(visited) != len(adj):
            return False

        # Passou em tudo! É a solução!
        state.board.forbid_edges(state.board.global_forbidden)
        state.board.draw_edges(state.board.global_drawn)
        return True

    def h(self, node) -> float:
        pass


        


if __name__ == "__main__":
    # TODO:
    # Ler o ficheiro do standard input,
    # Usar uma técnica de procura para resolver a instância,
    # Retirar a solução a partir do nó resultante,
    # Imprimir para o standard output no formato indicado.

    board = Board.parse_instance()

























































































# def is_globally_closed(self, state:SlitherlinkState):
#     """verifica se todos os vertices sao grau 2, quer dizer que temos uma
#     board compeltamente fechada, podendo ter mais do que 1 loop"""
#     #{edge: (v1 connect, v2 connect)}
#     connectivity = state.board.get_edges_connectivity()
#     for _ , ((_, v1_conn), (_, v2_conn)) in connectivity.items():
#         if v1_conn != 2 or v2_conn != 2:
#             return False
#     #caso todos os vertices sejam grau 2, temos uma forma fechada
#     return True

#def is_single_loop(self, state : SlitherlinkState):
#     """presupomos que state contem uma board previamente testadas por 
#     is_closed_form, que verifica se todos os vertices relevantes sao 
#     grau 2. Agora temos de verificar se todas as edges teem conexao"""

#     #a starting point
#     first_edge = list(state.board.all_drawn_edges)[0]

#     #vamos seguir o conjunto de linhas conectadas ate completar a volta, 
#     #seguindo sempre por vertice 1, ate voltarmos a first_edge
#     check = True
#     current_edge = first_edge
#     visited_edges = {first_edge}
#     while check:
#         v1 = state.board.get_edge_vertices()[0]
#         (_, drawn, _) = state.board.get_edges_around_vertex(v1)
#         #drawn tem 2 edges, a atual, e a nova. vamos pegar na nova
#         new_edge = drawn - current_edge
#         #se new edge for inicial, acabamos o loop
#         if new_edge == first_edge:
#             check = False
#             continue
#         #caso contrario, adicionar visited edge, e dar net a nova
#         #current edge
#         visited_edges.add(new_edge)
#         current_edge = new_edge
    
#     #depois de concluir um loop, visited_edges tem de ser igual a
#     #board.all_drawn_edges()
#     if state.board.all_drawn_edges() == visited_edges:
#         return True
#     else: return False