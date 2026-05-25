from slitherlink import *

#Ler grelhadafigura 1a:
board= Board.parse_instance()

#Criar umainstânciadeSlytherlink:
problem = Slitherlink(board)

#Criar um estado com a configuração inicial:
initial_state = SlitherlinkState(board)

#Realizar ação deativaras arestasdacélula(2, 1)
result_state=s1 =problem.result(initial_state,[('h',2,1), ('v',2, 1), ('v',2, 2)])

print(result_state.board.get_inactive_edges(2,1))

#Mostrar valor naposição(2, 1):
print(result_state.board.get_active_edges(2, 1))
print(result_state.board.get_inactive_edges(2,1))
#print(result_state.board.print_complete())