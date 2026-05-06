from slitherlink import Board, SlitherlinkState
from constraint_propagator import ConstraintPropagator

#Realizado com recurso a Deepseek
class EdgeTriggerResolver:
    """
    Resolve ambiguidades em padrões complexos, usando lógica de "trigger edges" (desenhadas a verde no esquema)

    Usa os padrões formados pelas "arestas obrigatórias" (desenhadas a azul no esquema), já identificadas, e resolve as ambiguidades que persistirem dentro dessas
    """

    def __init__(self, state: SlitherlinkState):
        """
        Inicia o solver com o estado atual
        """

        self.state = state
        self.board = state.board

        self.propagator = ConstraintPropagator(state)
    
    def find_trigger_edge(self, pattern_edges: set) -> tuple:
        """
        Encontra uma trigger edge entre as arestas já desenhadas
        """

        drawn_edges = self.board.all_drawn_edges
        for edge in pattern_edges:
            if edge in drawn_edges:
                return edge
        return None
    
    
    def resolve_adjacent_3_3(self, cell1:tuple, cell2:tuple, trigger_edge:tuple = None) -> set:
        """
        Resolve ambiguidade de padrão para células 3-3 adjacentes, usando as arestas obrigatórias do progador e decidir qual dos padrões por elas formado é o correto
        """
        #Obter arestas obrigatórias do propagador para este caso particular
        
        mandatory = self.propagator.mandatory_3_3_edges()

        #Encontrar as arestas obrigatórias que se encontram na região entre a célula 1 e a célula 2
        r1, c1 = cell1
        r2, c2 = cell2

        relevant_edges = set()
        for edge in mandatory:
            t, er, ec = edge
            if r2 < r1: #vertical com célula 2 acima
                if t == 'h' and (er == r1-1 or er == r1 or er == r1+1) and ec == c1:
                    relevant_edges.add(edge)
            elif r2 > r1: #vertical com célula 2 abaixo
                if t == 'h' and (er == r1 or er == r1+1 or er== r1+2) and ec == c1:
                    relevant_edges.add(edge)
            elif c2 < c1: #horizontal com célula 2 à esquerda
                if t== 'v' and (ec == c1-1 or ec == c1 or ec == c1+1) and er == r1:
                    relevant_edges.add(edge)
            elif c2 > c1: #horizontal com célula 2 à direita
                 if t== 'v' and (ec == c1-1 or ec == c1 or ec == c1+1) and er == r1:
                     relevant_edges.add(edge)
        
        #Decisão baseada na trigger edge
        if trigger_edge in relevant_edges:
            #A trigger edge é uma das obrigatórias - usar todas as obrigatórias
            return relevant_edges
        else:
            #Sem trigger clara, devolver todas as obrigatórias
            return relevant_edges
        
    def resolve_diagonal_3_3(self, cell1: tuple, cell2:tuple, trigger_edge: tuple = None) -> set:
        """
        Resolve ambiguidade entre células 3 e 3 na diagonal.

        Usa as arestas obrigatórias (azul no esquema, case_3_3_diagonal_edges no constraint_propagator) e decide qual das soluções é correta de acordo com a posição da "trigger edge" (verde no esquema).
        """

        r1, c1 = cell1
        r2, c2 = cell2

        #Obter os padrões de arestas obrigatórias do propagador para as diagonais 3-3
        mandatory, _ = self.propagator.case_3_3_diagonal_edges()

        #Identificar qual o padrão diagonal que está na região destas células
        pattern_tl_br = set()
        pattern_tr_bl = set()

        for edge in mandatory:
            t, er, ec = edge
            #Padrão TL-BR (Top-Left para Bottom-Right)
            if(t == 'h' and er == r1 and ec == c1) or \
              (t == 'v' and er == r1 and ec == c1) or \
              (t == 'h' and er == r1+2 and  ec == c1+1) or \
              (t == 'v' and er == r1+1 and ec == c1+2):
                pattern_tl_br.add(edge)
            
            #Padrão TR-BL (Top-Right para Bottom-Left)
            if(t == 'h' and er == r1 and ec == c1+1) or \
              (t == 'v' and er == r1 and ec == c1+2) or \
              (t == 'h' and er == r1+2 and  ec == c1) or \
              (t == 'v' and er == r1+1 and ec == c1):
                pattern_tr_bl.add(edge)

        #Verificar qual dos padrões está ativo (considerando a posição da trigger edge)
        if trigger_edge is None:
            trigger_edge = self.find_trigger_edge(pattern_tl_br.union(pattern_tr_bl))

        if trigger_edge in pattern_tr_bl:
            return pattern_tr_bl
        elif trigger_edge in pattern_tl_br:
            return pattern_tl_br
        
        # Se não houver trigger edge, verificar a consistência com as arestas desenhadas
        drawn = self.board.all_drawn_edges

        if pattern_tl_br.issubset(drawn.union(self.board.allowed_edges)):
            # Evitar conflitos
            if not pattern_tl_br.intersection(self.board.unallowed_edges):
                return pattern_tl_br
        
        if pattern_tr_bl.issubset(drawn.union(self.board.allowed_edges)):
            # Evitar conflitos
            if not pattern_tr_bl.intersection(self.board.unallowed_edges):
                return pattern_tr_bl
        
        #Fallback: ambas podem ser validadas (caso raro)
        return pattern_tr_bl.union(pattern_tl_br)
    

    def resolve_case_3_0(self, cell3: tuple, cell0:tuple, trigger_edge: tuple = None) -> tuple:
        """
        Resolve a ambiguidade no caso 3-0 (células 3-0 adjacentes).
        
        Já tendo o propagador identificado as arestas obrigatórias (a azul no esquema) e as proibidas (a vermelho no esquema), escolhe-se agora a orientação 
        
        Return:
           (mandatory, forbidden = self.propagator.case_3_0_edges())
        """

        mandatory, forbidden = self.propagator.case_3_0_edges()

        r3, c3 = cell3
        r0, c0 = cell0

        #Filtrar arestas relevantes para este caso específico
        relevant_mandatory = set()
        relevant_forbidden = set()

        for edge in mandatory:
            t, er, ec = edge
            #Verificar se a edge está relacionada com as células
            cells_affected = self.board.cells_adjacent_to_action(edge)
            if ((r3, c3) or (r0, c0)) in cells_affected:
                relevant_forbidden.add(edge)
        
        if trigger_edge is None:
            trigger_edge = self.find_trigger_edge(relevant_mandatory)

        #Decisão baseada na trigger
        if trigger_edge in relevant_mandatory:
            #Usar todas as obrigatórias do caso
            return relevant_mandatory, relevant_forbidden
        else:
            #Verificar qual dos padrões é consistente
            return self._check_3_0_consistency(relevant_mandatory, relevant_forbidden)
        
    def _check_3_0_consistency(self, mandatory: set, forbidden: set) -> tuple:
        """
        Verifica a consistência das arestas 3-0 com o estado atual.
        """

        drawn = self.board.all_drawn_edges

        valid_mandatory = set()
        valid_forbidden = set()

        for edge in mandatory:
            if edge in drawn:
                valid_mandatory.add(edge)
            elif edge not in self.board.unallowed_edges:
                valid_mandatory.add(edge)

        for edge in forbidden:
            if edge not in drawn:
                valid_forbidden.add(edge)
        
        return valid_mandatory, valid_forbidden
    
    def resolve_complete(self) -> tuple:
        """
        Resolve todas as ambiguidades possíveis no estado atual
        
        Returns:
            (all mandatory, all forbidden) - todas as arestas determinadas
        """

        #obter todas as arestas obrigatórias e proibidas do propagador
        all_mandatory = self.propagator.mandatory_edges()
        all_forbidden = self.propagator.unallowed_edges()

        #Resolver ambiguidades diagonais
        board = self.board.board
        rows = len(board)
        cols = len(board[0])

        for r in range(rows - 1):
            for c in range(cols - 1):
                #Diagonal TL-BR
                if board[r][c] == 3 and board[r+1][c+1] == 3:
                    resolved = self.resolve_diagonal_3_3((r,c), (r+1, c+1))
                    #Remover as ambíguias e adicionar as  resolvidas
                    pattern_tl_br = self.propagator.case_3_3_diagonal_edges()[0]
                    #Atualizar all_mandatory
                    for edge in pattern_tl_br:
                        if edge in all_mandatory:
                            all_mandatory.discard(edge)
                    all_mandatory.update(resolved)

                #Diagonal TR-BR
                if board[r][c+1] == 3 and board[r+1][c] == 3:
                    resolved = self.resolve_diagonal_3_3((r,c+1), (r+1, c))
                    #Remover as ambíguias e adicionar as  resolvidas
                    pattern_tr_bl = self.propagator.case_3_3_diagonal_edges()[0]
                    #Atualizar all_mandatory
                    for edge in pattern_tr_bl:
                        if edge in all_mandatory:
                            all_mandatory.discard(edge)
                    all_mandatory.update(resolved)
            
        return all_mandatory, all_forbidden
