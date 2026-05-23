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
        pass

    def __hash__(self):
        pass

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

        #TODAS AS EDGES - PROIBIDAS
        self.allowed_edges = self.all_edges
        #EDGES PROIBIDAS
        self.unallowed_edges = set()

        #EDGES DESENHADAS AO LONGO DA PROCURA
        self.drawn_edges = set()
        #EDGES OBRIGATORIAS
        self.mandatory_drawn_edges = set()

    @property
    def all_drawn_edges(self):
        """ uniao de edges desenhadas e obrigatorias"""
        return self.drawn_edges | self.mandatory_drawn_edges


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
        prohibited = relevant_edges.intersection(self.unallowed_edges)

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

    #METODO DE COPY

    #AIAIAIAIAIAAIAIAIAIIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIAIA
    def copy(self):
        """
        Cria uma cópia profunda (deep copy) do estado do tabuleiro atual.
        Essencial para a procura em árvore (DFS) não sobrepor estados.
        """
        # 1. Cria um novo tabuleiro usando o mesmo layout base
        novo_tabuleiro = Board(self.board)
        
        # 2. Copia as variáveis de estado (os sets) para a nova memória
        novo_tabuleiro.allowed_edges = self.allowed_edges.copy()
        novo_tabuleiro.unallowed_edges = self.unallowed_edges.copy()
        novo_tabuleiro.drawn_edges = self.drawn_edges.copy()
        novo_tabuleiro.mandatory_drawn_edges = self.mandatory_drawn_edges.copy()
        
        return novo_tabuleiro


    def print(self) -> str:
        """
        Retorna a representação do tabuleiro no formato de output exigido:
        4 bits por célula (top, right, bottom, left), separados por tabulação (\t).
        """

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
    # def __init__(self, board: Board, gui=None):
    #     """O construtor especifica o estado inicial."""

    #     self.gui = gui

    #     # ----------  edges obrigatorias e proibidas ------------
    #     from initial_propagator import InitialPropagator
    #     temp_state = SlitherlinkState(board)
    #     propagator = InitialPropagator(temp_state)

    #     # obter constrainsts
    #     forbidden = propagator.unallowed_edges() #- Passou a comentário de modo a dar lugar ao que está abaixo
    #     mandatory = propagator.mandatory_edges() 

    #     # #Feita alteração de modo a incluir o EdgeTriggerResolver
    #     # resolver = EdgeTriggerResolver(temp_state)
    #     # mandatory, forbidden = resolver.resolve_complete()

    #     #remover proibicoes removendo as edges proibidas de allowed_edges
    #     #parece complicado, mas assim temos os forbidden, com verificacao que todas as 
    #     #edge coordinates percencem a borda. mais por questao de consistencia
    #     board.unallowed_edges = board.allowed_edges - (board.allowed_edges - set(forbidden))
    #     board.allowed_edges = board.allowed_edges - set(forbidden)
    #     #guardar as mandatory edges
    #     board.mandatory_drawn_edges = mandatory

    #     #print para eu visualizar
    #     print("Mandatory Edges")
    #     print(board.print_complete())

    #     # com errou a correr example 4 percebi que para seguir o template
    #     #em search.py e necessario esta variavel self.initial
    #     initial_state = SlitherlinkState(board)
    #     self.initial = initial_state

    def __init__(self, board: Board, gui=None):
        """O construtor especifica o estado inicial."""
        self.gui = gui

        # 1. Correr o Propagador Inicial (Padrões fixos dos números)
        from initial_propagator import InitialPropagator
        from SATOracle import ConstraintPropagator
        
        # O InitialPropagator precisa do estado, mas vamos passá-lo provisoriamente
        temp_state = SlitherlinkState(board)
        init_propagator = InitialPropagator(temp_state)

        forbidden = init_propagator.unallowed_edges()
        mandatory = init_propagator.mandatory_edges()

        # Injetar as deduções do InitialPropagator na Board
        board.unallowed_edges = board.allowed_edges - (board.allowed_edges - set(forbidden))
        board.allowed_edges = board.allowed_edges - set(forbidden)
        board.mandatory_drawn_edges = mandatory
        
        # Colocamos tudo no drawn_edges para que o ConstraintPropagator 
        # consiga usar essas arestas para calcular o grau (v_conn)
        board.drawn_edges.update(mandatory)

        # 2. Correr o NOVO Motor de Dedução (Efeito Cascata)
        propagator = ConstraintPropagator(board)
        allowed_actions = propagator.propagate()

        print("Tabuleiro Inicial após Propagação (Initial + Cascata):")
        print(board.print_complete())

        # 3. Criar o estado inicial verdadeiro
        initial_state = SlitherlinkState(board)
        
        # 4. Guardar as jogadas válidas para a DFS arrancar
        if allowed_actions is False:
            initial_state.is_valid = False
            initial_state.allowed_actions = []
        else:
            initial_state.is_valid = True
            initial_state.allowed_actions = allowed_actions
            
        self.initial = initial_state
    
    #AIAIAIAIAIAIAIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIAIAIAIIAIAIAIAIAIAIIA
    def actions(self, state: SlitherlinkState):
        """Action needs to be:
        1) at a loose edge,
        2) is possible (respects squares, and vertices)
        """
        # 1. Beco sem saída detetado no result()
        if getattr(state, 'is_valid', True) is False:
            return []
        
        print(state.board.print_complete())
            
        # 2. A cobra está em andamento (O propagador já nos deu as opções!)
        if hasattr(state, 'allowed_actions') and state.allowed_actions:
            # Retornamos a lista do que é permitido para continuar a cobra
            return list(state.allowed_actions)
            
        # 3. O Jogo Acabou (Cobra fechou e não há ações pendentes)
        if state.board.all_drawn_edges and not getattr(state, 'allowed_actions', None):
            return []
            
        # 4. Primeira jogada do jogo (O tabuleiro está vazio ou só tem deduções iniciais)
        if not state.board.all_drawn_edges:
            possiveis = state.board.allowed_edges - state.board.unallowed_edges
            if possiveis:
                # CORREÇÃO: Devolver a lista TODA para a procura ter opções
                return list(possiveis) 
                
        return []

    def result(self, state, action):
        """adiciona uma action que foi selecionada em actions, e faz a
        constrains propagation"""

        from SATOracle import ConstraintPropagator

        #copiar board, board atual tem de ficar intacta pois representa
        #estado anterior
        new_board = state.board.copy() 
        
        new_board.drawn_edges.add(action) #adicionar acao
        
        #correr propagator, e verificar se acao levou a board invalida de continuar
        propagator = ConstraintPropagator(new_board)

        # Se o propagador detetou uma contradição (False), marcamos este estado 
        # como um beco sem saída para que a search tree saiba que tem de recuar.
        is_valid = propagator.propagate()
        new_state = SlitherlinkState(new_board)
        if is_valid is False:
            #estado nao permitido, nao tem como continuar
            new_state.is_valid = False
        else:
            #estado permitido e vamos guardar as acoes permitidas
            new_state.is_valid = True
            new_state.allowed_actions = is_valid
            
        return new_state
    
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
        return True

    def h(self, node: Node):
        pass 
    
    def _has_premature_loop(self, board):
        pass


if __name__ == "__main__":
    # TODO:
    # Ler o ficheiro do standard input,
    # Usar uma técnica de procura para resolver a instância,
    # Retirar a solução a partir do nó resultante,
    # Imprimir para o standard output no formato indicado.

    board = Board.parse_instance()
