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
    
    
    def get_extremes(self):
        pass

    def get_actions_from_extreme(self, extreme_edge, allowed_edges):
        pass


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
    
    def actions(self, state: SlitherlinkState):
        pass
    
    def result(self, state, action):
        pass
    
    def _has_premature_loop(self, board):
        pass

    
    def goal_test(self, state: SlitherlinkState):
        pass

    
    def h(self, node: Node):
        pass 



if __name__ == "__main__":
    # TODO:
    # Ler o ficheiro do standard input,
    # Usar uma técnica de procura para resolver a instância,
    # Retirar a solução a partir do nó resultante,
    # Imprimir para o standard output no formato indicado.

    board = Board.parse_instance()
