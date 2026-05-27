import sys
import tkinter as tk
from slitherlink import Board, SlitherlinkState, Slitherlink
from slitherlink_gui import SlitherlinkGUI
from search import *
import time
import SATOracle

def main():
    board = Board.parse_instance()
    board_list = board.board

    print("Starting search...")
    start_time = time.perf_counter()

    problem = Slitherlink(board)
    problem.node_count = 0
    problem.t_loop = 0.0
    problem.t_sat = 0.0
    problem.total_result_time = 0.0

    original_result = problem.result
    original_loop = problem._has_premature_loop
    original_sat_propagate = SATOracle.SATSolver.propagate

    def loop_with_timer(board):
        t = time.perf_counter()
        res = original_loop(board)
        problem.t_loop += time.perf_counter() - t
        return res

    problem._has_premature_loop = loop_with_timer

    def sat_with_timer(self):
        t = time.perf_counter()
        res = original_sat_propagate(self)
        problem.t_sat += time.perf_counter() - t
        return res

    SATOracle.SATSolver.propagate = sat_with_timer

    def result_with_counter(state, action):
        problem.node_count += 1
        t0 = time.perf_counter()
        res = original_result(state, action)
        problem.total_result_time += time.perf_counter() - t0

        if problem.node_count % 5000 == 0:
            n = problem.node_count
            avg_total = problem.total_result_time / n * 1000
            avg_loop  = problem.t_loop / n * 1000
            avg_sat   = problem.t_sat / n * 1000
            avg_copy  = avg_total - avg_loop - avg_sat
            elapsed   = time.perf_counter() - start_time
            print(f"[DEBUG] Nós: {n} | "
                  f"total: {avg_total:.2f}ms | "
                  f"SAT: {avg_sat:.2f}ms | "
                  f"loop: {avg_loop:.2f}ms | "
                  f"copy: {avg_copy:.2f}ms | "
                  f"elapsed: {elapsed:.2f}s")

        return res

    problem.result = result_with_counter

    goal_node = greedy_search(problem)

    end_time = time.perf_counter()
    print(f"\nSolution found in {end_time - start_time:.4f} seconds!")
    print(f"[DEBUG] Total de nós explorados: {problem.node_count}")
    if problem.node_count:
        n = problem.node_count
        avg_total = problem.total_result_time / n * 1000
        avg_loop  = problem.t_loop / n * 1000
        avg_sat   = problem.t_sat / n * 1000
        avg_copy  = avg_total - avg_loop - avg_sat
        print(f"[DEBUG] Avg total por nó : {avg_total:.2f}ms")
        print(f"[DEBUG] Avg SAT   por nó : {avg_sat:.2f}ms")
        print(f"[DEBUG] Avg loop  por nó : {avg_loop:.2f}ms")
        print(f"[DEBUG] Avg copy  por nó : {avg_copy:.2f}ms")

    root = tk.Tk()
    app = SlitherlinkGUI(root, board_list)

    raw_solution_string = goal_node.state.board.print()
    sol_grid = [line.split('\t') for line in raw_solution_string.split('\n')]
    app.load_solution(sol_grid)
    root.mainloop()

if __name__ == "__main__":
    main()
