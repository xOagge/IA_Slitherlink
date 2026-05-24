# como pensado em pensamento com o gemini pro (perguntei e ele verificou se seria uma boa
#forma de organizar o codigo, o ConstraintPropagator vai receber uma board, e para um tal
#estado verificar as obrigatorias e proibidas acoes seguintes)

#PODE E TEM DE SER PESADAMENTE OPTIMIZADO, O PROPAGATE DA RUN A BOARD TODA, DEVE HAVER MANEIRA MAIS RAPIDA
#DE ITERAR APENAS ONDE PRECISO

class ConstraintPropagator:
    def __init__(self, Board):
        self.Board = Board

    #AIAIAIAIAIAIAIAIAIAIAIAIAI PARITY RULES
    def apply_parity_constraints(self):
        """
        Parity rule: the loop is a closed curve, so it must cross any straight
        cut-line an EVEN number of times.

        Two cut-lines exist naturally in a square grid:
        - Each row r: the vertical edges ('v', r, 0..cols) form a horizontal cut.
        The loop crosses this cut an even number of times.
        - Each col c: the horizontal edges ('h', 0..rows, c) form a vertical cut.
        The loop crosses this cut an even number of times.

        When exactly one edge in a cut is still unknown, we can force it:
        - remaining known LINEs are ODD  → the unknown MUST be LINE  (to make total even)
        - remaining known LINEs are EVEN → the unknown MUST be CROSS (total already even)
        """
        mandatory = set()
        unallowed = set()
        board = self.Board

        # --- Row cuts: vertical edges across each row ---
        for r in range(board.rows):
            cut = [('v', r, c) for c in range(board.cols + 1)]
            cut = [e for e in cut if e in board.all_edges]

            line_count = sum(1 for e in cut if e in board.all_drawn_edges)
            unknown = [e for e in cut
                    if e not in board.all_drawn_edges
                    and e not in board.all_forbidden_edges]

            if len(unknown) == 1:
                e = unknown[0]
                if line_count % 2 == 1:   # odd lines → need one more to make even
                    mandatory.add(e)
                else:                      # even lines already → adding one breaks it
                    unallowed.add(e)

        # --- Column cuts: horizontal edges down each column ---
        for c in range(board.cols):
            cut = [('h', r, c) for r in range(board.rows + 1)]
            cut = [e for e in cut if e in board.all_edges]

            line_count = sum(1 for e in cut if e in board.all_drawn_edges)
            unknown = [e for e in cut
                    if e not in board.all_drawn_edges
                    and e not in board.all_forbidden_edges]

            if len(unknown) == 1:
                e = unknown[0]
                if line_count % 2 == 1:
                    mandatory.add(e)
                else:
                    unallowed.add(e)

        return (unallowed, mandatory)

    def apply_vertex_local_constraints(self, v_coords, v_conn):
        """esta funcao aplica logica as edges locais a um vertex, de forma
        a decidir que edges sao obrigatorias desenhar, proibidas, ou permitidas(
        candidatas a acao)"""
        mandatory = set()
        unallowed = set()
        allowed = set()
        (prohibited, drawn , undrawn) = self.Board.get_edges_around_vertex(v_coords)
        total_edges = len(prohibited) + len(drawn) + len(undrawn) #em cantos pode ser 3 ou 2

        #Hard Constraint
        if v_conn > 2:
            return False
        
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
        Aplica a lógica do Slitherlink às células.
        Agora também previne loops 1x1 em células vazias!
        """
        mandatory = set()
        unallowed = set()
        
        edges = self.Board.get_cell_edges(r, c)
        
        drawn = [e for e in edges if e in self.Board.all_drawn_edges]
        prohibited = [e for e in edges if e in self.Board.all_forbidden_edges]
        undrawn = [e for e in edges if e not in drawn and e not in prohibited]
        
        #se tem 3 arestas desenhadas, proibir a proxima
        if len(drawn) == 3: unallowed.update(undrawn)
        #se tem 4 arestas desenhadas, board is dead end
        if len(drawn) == 4: return False 
            
        # celula vazia nao tem regras de restricoes, exceto 1x1 loop
        if cell_value == "." or cell_value == -1:
            return (unallowed, mandatory)
            
        
        # se desenhamos mais do que permitido / permitidas sao menos do que necessario
        #entao board is dead end
        if len(drawn) > cell_value or len(drawn) + len(undrawn) < cell_value:
            return False
            
        #se  numero desenhadas vai de acordo com celula, proibir restantes
        if len(drawn) == cell_value:
            unallowed.update(undrawn)
            
        #se todas as perimitidas somarem cell value, temos de desenhar todas
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

            #get relevant vertices
            relevant_edges = self.Board.recently_changed_edges
            if not relevant_edges:
                break
            relevant_vertices = {v for edge in relevant_edges for v in self.Board.get_edge_vertices(edge)}
            relevant_cells = {cell for edge in relevant_edges for cell in self.Board.cells_adjacent_to_edge(edge)}
            #print(relevant_cells)

            # 1) DIRECT CELL LOGIC, DIRECT LOGIC
            for vertice in relevant_vertices:
                #get vertex degree
                (_, drawn, _) = self.Board.get_edges_around_vertex(vertice)
                v_degree = len(drawn)
                #apply vertex local constraints
                res1 = self.apply_vertex_local_constraints(vertice, v_degree)
                #apply and save logic
                if res1 is False: return False
                (un, mand, allo) = res1
                unallowed.update(un)
                mandatory.update(mand)
                allowed.update(allo)
            
            #AIAIAIAIAIAIAIA, CELL PROPAGATION RULES ALL BOARD
            for cell in relevant_cells:
                r, c = cell
                cell_val = self.Board.board[r][c]
                if cell_val != "." and cell_val != -1:
                    res_cell = self.apply_cell_local_constraints(r, c, int(cell_val))
                    if res_cell is False: return False # Regra quebrada!
                    
                    unallowed.update(res_cell[0])
                    mandatory.update(res_cell[1])
            
            # 2) PATTERN LOGIC
            # PP = PatternPropagator(self.Board)
            # mandatory.update(PP.mandatory_edges())
            # unallowed.update(PP.[1])
            
            
            # SECTOR PARITY CONSTRAINTS
            res_sector = self.apply_parity_constraints()
            if res_sector is False: return False
            unallowed.update(res_sector[0])
            mandatory.update(res_sector[1])

            #se ha uma edge amba obrigatoria e proibida, board esta estragada, beco sem saida
            if not mandatory.isdisjoint(unallowed):
                return False
            
            #desenhar obrigatorios e proibidos  
            self.Board.recently_changed_edges = set()
            if mandatory:
                self.Board.draw_edges(mandatory)
            if unallowed:
                self.Board.forbid_edges(unallowed) # Sem isto, não há efeito cascata!

            #se nao foi adicionado obrigatorios ou proibidos, a board fica igual e acabamos o loop
            if len(mandatory) == 0 and len(unallowed) == 0:
                changed = False

        return allowed




    # #constraints logics
    # def propagate(self):
    #     """propaga as edges proibidas, obrigatorias
    #     e as opcionais (acoes possiveis). E um loop que apenas termina
    #     quando nao ha alteracoes, isto pois alterar regras num vertex 2, pode 
    #     alterar as edges de um vertex 1, processado apriori, entao temos de voltar
    #     ao 1 para processar de novo"""

    #     mandatory = set()
    #     unallowed = set()
    #     allowed = set()

    #     changed = True
    #     #enquanto houver alteracoes, aplicar
    #     while changed:
    #         mandatory = set()
    #         unallowed = set()
    #         allowed = set()

    #         #get relevant vertices
    #         relevant_edges = self.Board.recently_changed_edges()
    #         relevant_vertices = {v for edge in relevant_edges for v in self.board.get_edge_vertices(edge)}

    #         # 1) DIRECT CELL LOGIC, DIRECT LOGIC
    #         for r in range(self.Board.rows + 1):
    #             for c in range(self.Board.cols + 1):
    #                 #get vertex degree
    #                 (_, drawn, _) = self.Board.get_edges_around_vertex((r,c))
    #                 v_degree = len(drawn)
    #                 #apply vertex local constraints
    #                 res1 = self.apply_vertex_local_constraints((r,c), v_degree)
    #                 #apply and save logic
    #                 if res1 is False: return False
    #                 (un, mand, allo) = res1
    #                 unallowed.update(un)
    #                 mandatory.update(mand)
    #                 allowed.update(allo)
            
    #         #AIAIAIAIAIAIAIA, CELL PROPAGATION RULES ALL BOARD
    #         for r in range(self.Board.rows):
    #             for c in range(self.Board.cols):
    #                 cell_val = self.Board.board[r][c]
    #                 if cell_val != "." and cell_val != -1:
    #                     res_cell = self.apply_cell_local_constraints(r, c, int(cell_val))
    #                     if res_cell is False: return False # Regra quebrada!
                        
    #                     unallowed.update(res_cell[0])
    #                     mandatory.update(res_cell[1])
            
    #         # 2) PATTERN LOGIC
    #         # PP = PatternPropagator(self.Board)
    #         # mandatory.update(PP.mandatory_edges())
    #         # unallowed.update(PP.[1])
            
            
    #         # SECTOR PARITY CONSTRAINTS
    #         res_sector = self.apply_parity_constraints()
    #         if res_sector is False: return False
    #         unallowed.update(res_sector[0])
    #         mandatory.update(res_sector[1])

    #         #se ha uma edge amba obrigatoria e proibida, board esta estragada, beco sem saida
    #         if not mandatory.isdisjoint(unallowed):
    #             return False
            
    #         #desenhar obrigatorios e proibidos  
    #         if mandatory:
    #             self.Board.draw_edges(mandatory)
    #         if unallowed:
    #             self.Board.forbid_edges(unallowed) # Sem isto, não há efeito cascata!

    #         #se nao foi adicionado obrigatorios ou proibidos, a board fica igual e acabamos o loop
    #         if len(mandatory) == 0 and len(unallowed) == 0:
    #             changed = False

    #     return allowed
    

# class PatternPropagator:
#     """similar to InitalPropagator, receives a board, we look for patterns,
#     and apply changes that are not directly applied due to vertex logic, but here
#     we take care of cases where we already have drawn and forbidden edges, unlike 
#     initialPropagator, which only receives a blank board, even though is extremelly 
#     helpfull to reduce combinatory by drawing mandatory glo0bal actions, there are 
#     some relative obligatory actions, which are taken care of here. Some inspirations
#     come from jonathanolson.net, which displays some cases"""
#     def __init__(self, Board):
#         self.Board = Board

#     def mandatory_edges(self) -> tuple:
#         return

#     def all_forbidden_edges(self) -> tuple:
#         return self.incoming_3_cell()

#     def incoming_3_cell(self):
#         """case: a cell 3, with no drawn edges around, and one vertex has 1 drawn edge.
#         that means that we will need to force it going aroudn the 3, as it cant complete
#         later, so we forbid the other edge at the vertex that has the drawn edge that is 
#         not near the 3. this way, we make it obligaotyr for this loose edge to go aroudn the 3,
#         and the propagate logic takes care of makignsure it goes around"""
#         pass



































