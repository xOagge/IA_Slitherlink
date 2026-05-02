from slitherlink import *

#Ler grelha da figura 1a:
board = Board.parse_instance()

#Criar umainstânciadeSlytherlink:
problem = Slitherlink(board)

#Obter o nó solução usando a procura em profundidade:
goal_node = depth_first_tree_search(problem)

#Verificar se foi atingida a solução
print("Is goal?", problem.goal_test(goal_node.state))
print("Solution:\n", goal_node.state.board.print(), sep="")
print("Solution:\n", goal_node.state.board.print_pretty(), sep="")