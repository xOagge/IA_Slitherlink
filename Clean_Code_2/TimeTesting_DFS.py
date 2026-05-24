import os
import time
import copy
import multiprocessing
import slitherlink

from slitherlink import Board, Slitherlink
from search import (
    depth_first_tree_search,
    recursive_best_first_search
)


def worker(algo, board, return_dict):
    problem = Slitherlink(board)

    start = time.perf_counter()

    try:
        result = algo(problem)
        status = "Solved" if result else "Failed"
    except Exception:
        status = "Error"

    end = time.perf_counter()

    return_dict["time"] = end - start
    return_dict["status"] = status


def run_once(algo, board, timeout=30):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    p = multiprocessing.Process(
        target=worker,
        args=(algo, board, return_dict)
    )

    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return timeout, "Timeout"

    return (
        return_dict.get("time", timeout),
        return_dict.get("status", "Error")
    )


def main():

    algorithms = {
        "DFS Tree": depth_first_tree_search,
        "DFS Recursive": recursive_best_first_search
    }

    RUNS = 10
    TIMEOUT = 30

    for i in range(1, 10):
        filename = f"test{i:02d}.txt"

        if not os.path.exists(filename):
            print(f"{filename} missing")
            continue

        with open(filename, "r") as f:
            slitherlink.stdin = f
            board_template = Board.parse_instance()

        print(f"\n=== {filename} ===")

        for name, algo in algorithms.items():
            times = []

            for run in range(RUNS):
                board = copy.deepcopy(board_template)

                t, status = run_once(algo, board, timeout=TIMEOUT)
                times.append(t)

                print(f"{name} | run {run+1}/10 | {status:<8} | {t:.4f}s")

            avg = sum(times) / RUNS
            print(f"{name} AVG: {avg:.4f}s\n")


if __name__ == "__main__":
    main()