from slitherlink import *

board = Board.parse_instance()

problem = Slitherlink(board)
initial_state = SlitherlinkState(board)
#SEGUNDO O EXAMPLE 2, ISTO DEVIA DAR 1, NAO SEI COMO EQ ISSO FARIA SENTIDO MAS TALVEZ PROXIMOS 
#EXERCICIOS AJUDARAO A PERCEBER PORQUE
print(initial_state.board.get_inactive_edges(2,1))

result_state = problem.result(initial_state,[('h',2,1),('v',2, 1),('v',2, 2)])
#Mostrar valor naposição(2, 1):
print(result_state.board.get_active_edges(2, 1))
print(result_state.board.get_inactive_edges(2,1))