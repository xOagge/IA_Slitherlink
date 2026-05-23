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
        (prohibited, _ , undrawn) = self.Board.get_edges_around_vertex(v_coords)
        if v_conn == 1:
            #if there is only 1 undrawn/ possible to draw
            if len(undrawn) == 1:
                edge = list(undrawn)[0]
                # e vai de acordo com regra de celulas
                if self.Board.is_action_possible(edge):
                    mandatory.add(edge) #e obrigatoria
                else:
                    unallowed.add(edge) #senao e proibida
            else: 
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

        return (unallowed, mandatory, allowed)

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

                (un, mand, allo) = self.apply_vertex_local_constraints(v1_coords, v1_conn)
                unallowed.update(un)
                mandatory.update(mand)
                allowed.update(allo)

                (un, mand, allo) = self.apply_vertex_local_constraints(v2_coords, v2_conn)
                unallowed.update(un)
                mandatory.update(mand)
                allowed.update(allo)

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

