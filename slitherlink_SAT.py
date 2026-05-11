#!/usr/bin/env python3
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
    
    def __lt__(self, other):
        return self.id < other.id

    # TODO: outros metodos da classe

    def get_board(self):
        return self.board
    
    # GEMINI PRO 
    def __eq__(self, other):
        # Se as duas boards têm exatamente o mesmo set de linhas desenhadas,
        # significa que o tabuleiro está visualmente idêntico.
        if not isinstance(other, SlitherlinkState):
            return False
        return self.board.all_drawn_edges == other.board.all_drawn_edges

    def __hash__(self):
        # Transforma o set de edges numa versão 'congelada' (frozenset)
        # para que o algoritmo consiga usar isto como chave de memória rápida.
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

    # TODO: outros metodos da classe ----------------------------------

    def __init__(self, board:list):
        self.board:list = board
        self.rows:int = len(board) #row size
        self.cols:int = len(board[0]) #column size

        #sendo uma board NxM comprimento, temos 
        # N+1 rows e M columns de linhas horizontais 
        # N rows e M+1 columns de linhas verticais
        #range(X)-> [0,X-1], entao para ter K elementos, range(K)

        #esta definicao foi feita por gemini pro
        self.all_edges = {
            ('h', r, c) for r in range(self.rows + 1) for c in range(self.cols)
        } | {
            ('v', r, c) for r in range(self.rows) for c in range(self.cols + 1)
        }
        #vai ser aplicado constrainsts de proibicao
        self.allowed_edges = self.all_edges
        #guardar as edges nao permitidas
        self.unallowed_edges = set()

        # separados devido a prints serem apenas as manualmente desenhadas
        self.drawn_edges = set()
        #vai ser guardada as mandatory edges, imutavel
        self.mandatory_drawn_edges = set()


    @property
    def all_drawn_edges(self):
        """ uniao de edges desenhadas e obrigatorias"""
        return self.drawn_edges | self.mandatory_drawn_edges

    #exemplo retorna um numero
    def get_inactive_edges(self, row:int, column:int) -> int:
        """Devolve o número de arestas ativas"""
        count = 4
        for edge in self.all_drawn_edges:
            if edge == ('h',row, column) or edge == ('h',row+1, column) \
               or edge == ('v',row, column) or edge == ('v',row, column+1):
               count -= 1
        return count

    def get_all_edges(self):
        return self.all_edges
  
    def get_board(self): 
        return self.board

    def add_action(self, action):
        """ usado para adicionar uma acao ja verificada como plausivel """
        self.drawn_edges.add(action)

    def cells_adjacent_to_action(self, action):
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
    
    #Claude
    def get_extremes(self):
        """da return as extremidades do que ja temos desenhado"""
        extreme_edges = []
        for edge in self.all_drawn_edges:
            count_1 = 0
            count_2 = 0
            t, r, c = edge
            if t == 'h':
                for edge2 in self.all_drawn_edges:
                    t2, r2, c2 = edge2
                    if edge2 == edge: continue
                    if t2 == 'h':
                        if r == r2 and c-1 == c2: count_1 += 1
                        if r == r2 and c+1 == c2: count_2 += 1
                    if t2 == 'v':
                        if r-1 == r2 and c == c2 or r == r2 and c == c2:
                            count_1 += 1
                        if r-1 == r2 and c+1 == c2 or r == r2 and c+1 == c2:
                            count_2 += 1
            elif t == 'v':
                for edge2 in self.all_drawn_edges:
                    t2, r2, c2 = edge2
                    if edge2 == edge: continue
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
            # extremo: so conectado num lado
            if (count_1 == 1 and count_2 == 0) or (count_1 == 0 and count_2 == 1):
                extreme_edges.append(edge)
        return extreme_edges

    #Claude
    def get_actions_from_extreme(self, extreme_edge, allowed_edges):
        """para um extremo, devolve as acoes possiveis que continuam a partir dele"""
        t, r, c = extreme_edge
        candidate_actions = []

        if t == 'h':
            # lado esquerdo do extreme: edges que conectam ao vertice (r, c)
            candidates_left = [('h', r, c-1), ('v', r, c), ('v', r-1, c)]
            # lado direito do extreme: edges que conectam ao vertice (r, c+1)
            candidates_right = [('h', r, c+1), ('v', r, c+1), ('v', r-1, c+1)]
        elif t == 'v':
            # lado de cima do extreme: edges que conectam ao vertice (r, c)
            candidates_top = [('v', r-1, c), ('h', r, c), ('h', r, c-1)]
            # lado de baixo do extreme: edges que conectam ao vertice (r+1, c)
            candidates_bottom = [('v', r+1, c), ('h', r+1, c), ('h', r+1, c-1)]

        # juntar todos os candidatos
        all_candidates = []
        if t == 'h':
            all_candidates = candidates_left + candidates_right
        elif t == 'v':
            all_candidates = candidates_top + candidates_bottom

        # filtrar: tem de estar em allowed_edges e nao ja desenhada
        for action in all_candidates:
            if action in allowed_edges and action not in self.all_drawn_edges:
                candidate_actions.append(action)

        return candidate_actions


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

    def is_action_possible(self, action):
        cells_list = self.cells_adjacent_to_action(action)

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

    #FULL GEMINI PRO, FAZER IMPLEMENTACAO MANUAL
    def print(self) -> str:
        """
        Retorna a representação do tabuleiro no formato de output exigido:
        4 bits por célula (top, right, bottom, left), separados por tabulação (\t).
        """
        output_rows = []
        
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                # Verificar cada uma das 4 arestas da célula (0 ou 1)
                top = '1' if ('h', r, c) in self.drawn_edges else '0'
                right = '1' if ('v', r, c + 1) in self.drawn_edges else '0'
                bottom = '1' if ('h', r + 1, c) in self.drawn_edges else '0'
                left = '1' if ('v', r, c) in self.drawn_edges else '0'
                
                # Juntar os 4 bits da célula
                cell_repr = top + right + bottom + left
                row_cells.append(cell_repr)
                
            # Juntar todas as células da linha com um tab (\t)
            output_rows.append("\t".join(row_cells))
            
        # Juntar todas as linhas com um newline (\n)
        return "\n".join(output_rows)

    #FULL GEMINI FAST, UTIL PARA VISUALIZAR
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
            
            # Fallback seguro caso a variável unallowed_edges ainda não exista no board
            unallowed = getattr(self, 'unallowed_edges', set())
            
            for r in range(self.rows):
                # 1. Linha das arestas HORIZONTAIS e Vértices
                h_line = ""
                for c in range(self.cols):
                    h_line += "+"
                    if ('h', r, c) in self.all_drawn_edges:
                        h_line += "---"
                    elif ('h', r, c) in unallowed:
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
                    elif ('v', r, c) in unallowed:
                        v_line += "x"    # Representação visual da proibição vertical
                    else:
                        v_line += " "
                    
                    # Converter para string, mas imprimir espaço se for '-1'
                    val = str(self.board[r][c])
                    v_line += f" {val if val != '-1' else ' '} "
                
                # Última aresta vertical da linha
                if ('v', r, self.cols) in self.all_drawn_edges:
                    v_line += "|"
                elif ('v', r, self.cols) in unallowed:
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
                elif ('h', self.rows, c) in unallowed:
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

        self.gui = gui

        # ----------  edges obrigatorias e proibidas ------------
        from constraint_propagator import InitialPropagator
        from edge_trigger_resolver import EdgeTriggerResolver
        temp_state = SlitherlinkState(board)
        propagator = InitialPropagator(temp_state)

        # obter constrainsts
        forbidden = propagator.unallowed_edges() #- Passou a comentário de modo a dar lugar ao que está abaixo
        mandatory = propagator.mandatory_edges() 

        # #Feita alteração de modo a incluir o EdgeTriggerResolver
        # resolver = EdgeTriggerResolver(temp_state)
        # mandatory, forbidden = resolver.resolve_complete()

        #remover proibicoes removendo as edges proibidas de allowed_edges
        #parece complicado, mas assim temos os forbidden, com verificacao que todas as 
        #edge coordinates percencem a borda. mais por questao de consistencia
        board.unallowed_edges = board.allowed_edges - (board.allowed_edges - set(forbidden))
        board.allowed_edges = board.allowed_edges - set(forbidden)
        #guardar as mandatory edges
        board.mandatory_drawn_edges = mandatory

        #print para eu visualizar
        print("Mandatory Edges")
        print(board.print_complete())

        # com errou a correr example 4 percebi que para seguir o template
        #em search.py e necessario esta variavel self.initial
        initial_state = SlitherlinkState(board)
        self.initial = initial_state
    
    #ALTERAR TUDO DAQUI PARA BAIXO PARA NAO SER AI -------------------------------------------------------------------------
    def actions(self, state: SlitherlinkState):
        board = state.board
        
        # 1. Se o estado já foi marcado como morto (pelo loop killer ou propagator)
        if getattr(board, 'contradiction', False):
            return ()
        
        drawn = board.all_drawn_edges

        # (Opcional) Mantive o teu print original para debug
        print("\n--- A explorar o seguinte estado: ---")
        print(state.board.print_complete())

        # =================================================================
        # O MOTOR DE EXTREMIDADES (MRV - Minimum Remaining Values)
        # =================================================================
        if len(drawn) > 0:
            extremes = board.get_extremes()
            
            if extremes:
                best_feasible = []
                min_options = 999
                
                # Passo 1: Avaliar todas as pontas soltas
                for extreme in extremes:
                    continuations = board.get_actions_from_extreme(extreme, board.allowed_edges)
                    feasible = [a for a in continuations if board.is_action_possible(a)]
                    
                    # DEAD END CHECK INSTANTÂNEO:
                    # Se qualquer ponta não tem opções válidas, a cobra está presa. Matar o ramo.
                    if len(feasible) == 0:
                        return () 
                        
                    # LÓGICA MRV: Guardar apenas a ponta que tem o MENOR número de opções
                    if len(feasible) < min_options:
                        min_options = len(feasible)
                        best_feasible = feasible
                        
                # Passo 2: Retornar apenas as ações da ponta mais "estrangulada"
                # Isto impede a árvore de ramificar 3x quando a outra ponta só tem 1 jogada forçada.
                return tuple(best_feasible)

        # =================================================================
        # FALLBACK (Início do jogo, ou situações em que não há extremos)
        # =================================================================
        actions = board.allowed_edges - drawn
        adjacent_actions = []
        
        if len(drawn) != 0:
            for action in actions:
                if board.is_action_adjacent_to_edge(action):
                    adjacent_actions.append(action)
        else:
            # Primeira jogada do jogo: todas as permitidas são válidas
            adjacent_actions = list(actions)

        feasible_actions = [a for a in adjacent_actions if board.is_action_possible(a)]
        return tuple(feasible_actions)
    
    def result(self, state, action):
        from SATOracle import SATSolver

        board = state.get_board()
        newBoard = copy.deepcopy(board)

        if isinstance(action, tuple) and isinstance(action[0], str):
            newBoard.add_action(action)
        else:
            for act in action:
                newBoard.add_action(act)

        # 1. Run your SAT Solver / Propagator
        sat = SATSolver(newBoard)
        valid = sat.propagate()
        
        if not valid:
            newBoard.contradiction = True
        else:
            # 2. THE LOOP KILLER: Check if this action just closed a tiny loop
            if self._has_premature_loop(newBoard):
                newBoard.contradiction = True

        return SlitherlinkState(newBoard)

    #gemini helper para o result
    def _has_premature_loop(self, board):
        """
        Scans the board for any closed loops. 
        If it finds a closed loop that isn't the final answer, it returns True (Violation).
        """
        drawn = board.all_drawn_edges
        if not drawn: return False
        
        # Build a fast adjacency map of connected edges
        from collections import defaultdict
        adj = defaultdict(list)
        for edge in drawn:
            t, r, c = edge
            v1 = (r, c)
            v2 = (r, c + 1) if t == 'h' else (r + 1, c)
            adj[v1].append(edge)
            adj[v2].append(edge)
            
        visited_edges = set()
        
        # Search for connected components
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
            
            # Check if this specific component forms a closed loop 
            # (A loop is closed if EVERY vertex in it has exactly 2 edges touching it)
            is_closed = True
            for v in comp_vertices:
                if len(adj[v]) != 2:
                    is_closed = False
                    break
                    
            if is_closed:
                # WE FOUND A CLOSED LOOP!
                
                # Violation 1: It's a small loop disjointed from other lines
                if len(comp_edges) != len(drawn):
                    return True 
                    
                # Violation 2: It's a single loop, but there are still numbers on the board
                # that haven't been satisfied yet (meaning it closed too early).
                for r in range(board.rows):
                    for c in range(board.cols):
                        hint = board.board[r][c]
                        if hint != -1 and board.get_active_edges(r, c) != hint:
                            return True 
                            
        return False

    #FULL GEMINI
    def goal_test(self, state: SlitherlinkState):
        board = state.get_board()
        drawn_edges = board.all_drawn_edges

        # 1. Se o tabuleiro estiver vazio, obviamente não é o objetivo
        if len(drawn_edges) == 0:
            return False

        # 2. VERIFICAÇÃO DAS DICAS (Obrigatório)
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint != -1 and hint is not None: 
                    if board.get_active_edges(r, c) != int(hint):
                        return False

        # 3. VERIFICAÇÃO DO CIRCUITO FECHADO (Grau dos vértices = 2)
        vertex_degrees = {}
        for edge in drawn_edges:
            t, r, c = edge
            v1 = (r, c)
            v2 = (r, c + 1) if t == 'h' else (r + 1, c)
            vertex_degrees[v1] = vertex_degrees.get(v1, 0) + 1
            vertex_degrees[v2] = vertex_degrees.get(v2, 0) + 1

        for vertex, degree in vertex_degrees.items():
            if degree != 2:
                return False

        # ---------------------------------------------------------
        # 4. VERIFICAÇÃO DE LOOP ÚNICO (Impede múltiplas formas fechadas)
        # ---------------------------------------------------------
        # Usamos BFS para garantir que todas as arestas desenhadas estão conectadas
        visited = set()
        start_edge = next(iter(drawn_edges))
        queue = [start_edge]
        visited.add(start_edge)
        
        while queue:
            curr_edge = queue.pop(0)
            t, r, c = curr_edge
            v1 = (r, c)
            v2 = (r, c + 1) if t == 'h' else (r + 1, c)
            
            for next_edge in drawn_edges:
                if next_edge not in visited:
                    nt, nr, nc = next_edge
                    nv1 = (nr, nc)
                    nv2 = (nr, nc + 1) if nt == 'h' else (nr + 1, nc)
                    
                    if v1 in (nv1, nv2) or v2 in (nv1, nv2):
                        visited.add(next_edge)
                        queue.append(next_edge)
                        
        # Se o número de arestas conectadas for menor que o total, há loops disjuntos!
        if len(visited) != len(drawn_edges):
            return False

        # Se passou nos testes todos, consideramos que ganhou!
        board.drawn_edges = board.all_drawn_edges
        return True

    # GEMINI PRO
    def h(self, node: Node):
        board = node.state.get_board()
        
        # 1. Contar arestas ativas por célula (A tua lógica original)
        cell_active_edges = {}
        for edge in board.all_drawn_edges:
            t, r, c = edge
            if t == 'h':
                if r < board.rows: 
                    cell_active_edges[(r, c)] = cell_active_edges.get((r, c), 0) + 1
                if r - 1 >= 0: 
                    cell_active_edges[(r-1, c)] = cell_active_edges.get((r-1, c), 0) + 1
            elif t == 'v':
                if c < board.cols: 
                    cell_active_edges[(r, c)] = cell_active_edges.get((r, c), 0) + 1
                if c - 1 >= 0: 
                    cell_active_edges[(r, c-1)] = cell_active_edges.get((r, c-1), 0) + 1

        score = 0.0
        
        # 2. Avaliar as restrições das células (A tua lógica original otimizada)
        for r in range(board.rows):
            for c in range(board.cols):
                hint = board.board[r][c]
                if hint == -1:
                    continue
                
                active = cell_active_edges.get((r, c), 0)
                missing = hint - active
                
                if missing == 0:
                    score -= 5.0  # Célula completa: recompensa
                elif missing > 0:
                    score += missing * 3.0  # Faltam linhas: penaliza
                else:
                    score += 100.0  # Linhas a mais: estado impossível

        # -------------------------------------------------------------------
        # 3. O NOVO MOTOR DE CONECTIVIDADE (Para forçar a fechar o loop)
        # -------------------------------------------------------------------
        drawn_edges = board.all_drawn_edges
        if len(drawn_edges) > 0:
            # Descobrir onde estão as pontas soltas (vértices com grau 1)
            degree = {}
            for edge in drawn_edges:
                t, r, c = edge
                v1 = (r, c)
                v2 = (r, c + 1) if t == 'h' else (r + 1, c)
                
                degree[v1] = degree.get(v1, 0) + 1
                degree[v2] = degree.get(v2, 0) + 1
                
            loose_ends = [v for v, deg in degree.items() if deg == 1]
            
            # Penalização de Fragmentação: Queremos apenas 1 caminho (2 pontas soltas).
            # Se houver 4, 6, 8 pontas, o Greedy está a fazer asneira a espalhar linhas.
            if len(loose_ends) > 2:
                score += len(loose_ends) * 15.0 
                
            # O "Gap Closer": Se temos exatamente 2 pontas, qual é a distância entre elas?
            elif len(loose_ends) == 2:
                v1, v2 = loose_ends
                # Manhattan distance formula: |x1 - x2| + |y1 - y2|
                manhattan_dist = abs(v1[0] - v2[0]) + abs(v1[1] - v2[1])
                
                # Multiplicamos por 2.0 para que dar um passo na direção certa
                # baixe o score mais rápido do que dar um passo para longe.
                score += manhattan_dist * 2.0 
                
            # Se houver 0 pontas soltas, mas as dicas ainda não estão completas (missing > 0 em cima)
            # significa que fechou um mini-loop cedo demais. Penaliza pesadamente.
            elif len(loose_ends) == 0 and score > 0:
                score += 500.0

        return score


if __name__ == "__main__":
    # TODO:
    # Ler o ficheiro do standard input,
    # Usar uma técnica de procura para resolver a instância,
    # Retirar a solução a partir do nó resultante,
    # Imprimir para o standard output no formato indicado.

    board = Board.parse_instance()





    # def actions(self, state: SlitherlinkState):
    #     """Retorna uma lista de ações que podem ser executadas a
    #     partir do estado passado como argumento."""

    #     print("\n--- A explorar o seguinte estado: ---")
    #     print(state.board.print_complete())
    

    #     # ORDEM, FREE EDGES -> CONTINUACOES EM LINHA -> NAO EXCEDE VALOR DE CELULAS
    #     # esta ordem parece ser optimizada para dar narrow dawn das possibilidades

    #     # todas as acoes fisicamente disponiveis
    #     board = state.board
    #     actions = board.allowed_edges - board.all_drawn_edges

    #     #de todas as opcoes de acoes, vou encontrar as que sao adjacentes e ao criam branches
    #     adjacent_actions = []
    #     if len(board.all_drawn_edges) != 0:
    #         for action in actions:
    #             if board.is_action_adjacent_to_edge(action):
    #                 adjacent_actions.append(action)
    #     else: adjacent_actions = actions

    #     #avaliar acoes que nao quebrem as regras de limite de linhas a volta de uma celula
    #     feasable_actions = []
    #     for action in adjacent_actions:
    #         if board.is_action_possible(action): feasable_actions.append(action)
        
    #     return tuple(feasable_actions)