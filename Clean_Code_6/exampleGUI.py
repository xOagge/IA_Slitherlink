import tkinter as tk
import time
import cProfile
import pstats
import io

from slitherlink import Board, SlitherlinkState, Slitherlink
from slitherlink_gui import SlitherlinkGUI
from search import *


def wrap_problem_with_counters(problem: Slitherlink):
    """Monkey-patches result() and actions() to count calls and time spent."""
    stats = {
        "nodes_expanded":  0,   # calls to result()
        "actions_calls":   0,   # calls to actions()
        "result_time":     0.0,
        "actions_time":    0.0,
        "propagations":    0,   # optional, if you want to track rank_actions calls
    }

    _original_result  = problem.result
    _original_actions = problem.actions

    def counted_result(state, action):
        stats["nodes_expanded"] += 1
        t0 = time.perf_counter()
        node = _original_result(state, action)
        stats["result_time"] += time.perf_counter() - t0
        return node

    def counted_actions(state):
        stats["actions_calls"] += 1
        t0 = time.perf_counter()
        acts = _original_actions(state)
        stats["actions_time"] += time.perf_counter() - t0
        return acts

    problem.result  = counted_result
    problem.actions = counted_actions

    return stats


def main():
    board = Board.parse_instance()
    board_list = board.board

    problem = Slitherlink(board)
    counters = wrap_problem_with_counters(problem)

    print("Starting search...")
    overall_start = time.perf_counter()

    # ---- Profile block ----
    profiler = cProfile.Profile()
    profiler.enable()

    goal_node = depth_first_tree_search(problem)

    profiler.disable()
    # -----------------------

    overall_end = time.perf_counter()
    overall_time = overall_end - overall_start

    # --- Print summary ---
    print("\n" + "="*55)
    print(f"  OVERALL TIME       : {overall_time:.4f}s")
    print(f"  Nodes expanded     : {counters['nodes_expanded']}")
    print(f"  actions() calls    : {counters['actions_calls']}")
    print(f"  Time in result()   : {counters['result_time']:.4f}s  "
          f"({counters['result_time']/overall_time*100:.1f}%)")
    print(f"  Time in actions()  : {counters['actions_time']:.4f}s  "
          f"({counters['actions_time']/overall_time*100:.1f}%)")
    print("="*55)

    # --- Per-function breakdown (top 20 by cumulative time) ---
    print("\n  TOP 20 FUNCTIONS BY CUMULATIVE TIME")
    print("-"*55)
    stream = io.StringIO()
    ps = pstats.Stats(profiler, stream=stream)
    ps.strip_dirs()
    ps.sort_stats("cumulative")
    ps.print_stats(100)
    print(stream.getvalue())

    # --- GUI ---
    root = tk.Tk()
    app = SlitherlinkGUI(root, board_list)
    raw_solution_string = goal_node.state.board.print()
    sol_grid = [line.split('\t') for line in raw_solution_string.split('\n')]
    app.load_solution(sol_grid)
    root.mainloop()


if __name__ == "__main__":
    main()