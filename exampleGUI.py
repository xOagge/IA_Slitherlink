import sys
import tkinter as tk
from slitherlink import Board, SlitherlinkState, Slitherlink
from slitherlink_gui import SlitherlinkGUI
from search import * # (or whatever search you are using)

from constraint_propagator import ConstraintPropagator

def main():

    # --------------aplicar os constraints -------------------
    board = Board.parse_instance()

    #declare board
    board_list:list = board.get_board()

    #find solution
    problem = Slitherlink(board)

    # #blind
    # goal_node = depth_first_tree_search(problem)
    goal_node = depth_first_graph_search(problem)
    # goal_node = depth_first_graph_search(problem)
    # goal_node = breadth_first_tree_search(problem)
    # goal_node = breadth_first_graph_search(problem)
    # goal_node = uniform_cost_search(problem)
    # goal_node = depth_limited_search(problem)
    # goal_node = iterative_deepening_search(problem)
    
    # #heuristic
    # goal_node = astar_search(problem)
    # goal_node = greedy_search(problem)
    #goal_node = recursive_best_first_search(problem)

    # #local search
    # goal_node = hill_climbing(problem)
    # goal_node = simulated_annealing(problem)
    # goal_node = genetic_search(problem)

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