import sys
import tkinter as tk
from slitherlink import Board, SlitherlinkState, Slitherlink
from slitherlink_gui import SlitherlinkGUI
from search import depth_first_tree_search # (or whatever search you are using)

def main():
    #declare board
    board = Board.parse_instance()
    board_list:list = board.get_board()

    #find solution
    problem = Slitherlink(board)
    goal_node = depth_first_tree_search(problem)

    #Criar a GUIantes deiniciar o vosso program
    root= tk.Tk()
    app = SlitherlinkGUI(root, board_list)
    
    # 4. Format the solution string back into a 2D list for the GUI
    raw_solution_string = goal_node.state.board.print()
    sol_grid = [line.split('\t') for line in raw_solution_string.split('\n')]
    
    # 5. Load the solution into the app
    app.load_solution(sol_grid)

    # 6. TRIGGER THE DISPLAY (This keeps the window open!)
    root.mainloop()

if __name__ == "__main__":
    main()