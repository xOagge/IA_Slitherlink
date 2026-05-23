# como pensado em pensamento com o gemini pro (perguntei e ele verificou se seria uma boa
#forma de organizar o codigo, o ConstraintPropagator vai receber uma board, e para um tal
#estado verificar as obrigatorias e proibidas acoes seguintes)

#PODE E TEM DE SER PESADAMENTE OPTIMIZADO, O PROPAGATE DA RUN A BOARD TODA, DEVE HAVER MANEIRA MAIS RAPIDA
#DE ITERAR APENAS ONDE PRECISO

class ConstraintPropagator:
    def __init__(self, Board):
        self.Board = Board

    def apply_vertex_local_constraints(self, v_coords, v_conn):
        """esta funcao aplica logica as edges locais a um vertex, de forma
        a decidir que edges sao obrigatorias desenhar, proibidas, ou permitidas(
        candidatas a acao)"""
        mandatory = set()
        unallowed = set()
        allowed = set()
        (prohibited, drawn , undrawn) = self.Board.get_edges_around_vertex(v_coords)
        total_edges = len(prohibited) + len(drawn) + len(undrawn) #em cantos pode ser 3 ou 2
        if v_conn == 1:
            #se nao ha para onde desenhar, e false
            if len(undrawn) == 0:
                return False
            #if there is only 1 undrawn/ possible to draw
            elif len(undrawn) == 1:
                edge = list(undrawn)[0]
                # e vai de acordo com regra de celulas
                if self.Board.is_action_possible(edge):
                    mandatory.add(edge) #e obrigatoria
                else:
                    return False #senao a unica possivel e proibida, entao e dead-end
            elif len(undrawn) >= 2: 
                #para todas as edges possiveis segundo regras de vertices
                for edge in undrawn:
                    #se for de acordo com regra de celulas
                    if self.Board.is_action_possible(edge):
                        allowed.add(edge) #permitida
                    else:
                        unallowed.add(edge) #senao e proibida
        elif v_conn == 2:
            #all around edges are prohibited
            unallowed.update(undrawn)
        elif v_conn == 0:
            #conn==0, ou seja, 0 drawn, logo se 1 undrawn, resto e prohibited
            if len(undrawn) == 1:
                edge = list(undrawn)[0]
                unallowed.add(edge)

        return (unallowed, mandatory, allowed)

    def apply_cell_local_constraints(self, r, c, cell_value):
        """
        Aplica a lógica básica do Slitherlink aos quadrados numerados.
        """
        mandatory = set()
        unallowed = set()
        
        edges = self.Board.get_cell_edges(r, c)
        
        drawn = [e for e in edges if e in self.Board.all_drawn_edges]
        prohibited = [e for e in edges if e in self.Board.unallowed_edges]
        undrawn = [e for e in edges if e not in drawn and e not in prohibited]
        
        # Regra 1: Beco Sem Saída (Já tem linhas a mais, ou é impossível atingir o valor)
        if len(drawn) > cell_value or len(drawn) + len(undrawn) < cell_value:
            return False
            
        # Regra 2: Objetivo Cumprido (Trancar o resto)
        if len(drawn) == cell_value:
            unallowed.update(undrawn)
            
        # Regra 3: Linhas Obrigatórias (Precisamos de todas as que sobram)
        if len(drawn) + len(undrawn) == cell_value:
            mandatory.update(undrawn)
            
        return (unallowed, mandatory)

    #constraints logics
    def propagate(self):
        """propaga as edges proibidas, obrigatorias
        e as opcionais (acoes possiveis). E um loop que apenas termina
        quando nao ha alteracoes, isto pois alterar regras num vertex 2, pode 
        alterar as edges de um vertex 1, processado apriori, entao temos de voltar
        ao 1 para processar de novo"""

        mandatory = set()
        unallowed = set()
        allowed = set()

        changed = True
        #enquanto houver alteracoes, aplicar
        while changed:
            mandatory = set()
            unallowed = set()
            allowed = set()
            #{edge: (v1 connect, v2 connect)}
            edge_connectivity = self.Board.get_edges_connectivity()
            for _ , ((v1_coords, v1_conn), (v2_coords, v2_conn)) in edge_connectivity.items():

                res1 = self.apply_vertex_local_constraints(v1_coords, v1_conn)
                if res1 is False: return False
                (un, mand, allo) = res1
                unallowed.update(un)
                mandatory.update(mand)
                allowed.update(allo)

                res2 = self.apply_vertex_local_constraints(v2_coords, v2_conn)
                if res2 is False: return False
                (un, mand, allo) = res2
                unallowed.update(un)
                mandatory.update(mand)
                allowed.update(allo)

            # for r in range(self.Board.rows + 1):
            #     for c in range(self.Board.cols + 1):
            #         #get vertex degree
            #         (_, drawn, _) = self.Board.get_edges_around_vertex((r,c))
            #         v_degree = len(drawn)
            #         #apply vertex local constraints
            #         res1 = self.apply_vertex_local_constraints((r,c), v_degree)
            #         #apply and save logic
            #         if res1 is False: return False
            #         (un, mand, allo) = res1
            #         unallowed.update(un)
            #         mandatory.update(mand)
            #         allowed.update(allo)
            
            #AIAIAIAIAIAIAIA, CELL PROPAGATION RULES ALL BOARD
            for r in range(self.Board.rows):
                for c in range(self.Board.cols):
                    cell_val = self.Board.board[r][c]
                    if cell_val != "." and cell_val != -1:
                        res_cell = self.apply_cell_local_constraints(r, c, int(cell_val))
                        if res_cell is False: return False # Regra quebrada!
                        
                        unallowed.update(res_cell[0])
                        mandatory.update(res_cell[1])

            #se ha uma edge amba obrigatoria e proibida, board esta estragada, beco sem saida
            if not mandatory.isdisjoint(unallowed):
                return False
            
            #desenhar obrigatorios e proibidos  
            if mandatory:
                self.Board.drawn_edges.update(mandatory)
            if unallowed:
                self.Board.unallowed_edges.update(unallowed) # Sem isto, não há efeito cascata!

            #se nao foi adicionado obrigatorios ou proibidos, a board fica igual e acabamos o loop
            if len(mandatory) == 0 and len(unallowed) == 0:
                changed = False

        return allowed