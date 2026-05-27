from slitherlink import *

board = Board.parse_instance()

print(board.get_cell_edges(3,1))
print(board.get_cell_edges(4,4))
