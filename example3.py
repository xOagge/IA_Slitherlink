from slitherlink import *

#Ler grelha da figura 1a:
board = Board.parse_instance()

#Criar uma instância de Slytherlink:
problem = Slitherlink(board)

#Criar um estado com a configuração inicial:
s0= SlitherlinkState(board)

#Aplicar asaçõesque resolvem ainstância
s1 = problem.result(s0,[('h', 2,1),('v', 2,1),('v', 2,2)])
s2 = problem.result(s1,[('h', 3,0)])
s3 = problem.result(s2,[('h', 3,2)])

#Verificar se foi atingida a solução
print("Is goal?",problem.goal_test(s2))
print("Is goal?",problem.goal_test(s3))
print("ActualState:\n",s3.board.print(), sep="")