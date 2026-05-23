import sys
import os
import time
import tracemalloc
import copy
import multiprocessing
import slitherlink

sys.setrecursionlimit(20000)

from slitherlink import Board, SlitherlinkState, Slitherlink

from search import (
    depth_first_tree_search,
    depth_first_graph_search
)


def search_worker(algo, fresh_board, return_dict):
    problem = Slitherlink(fresh_board)

    tracemalloc.start()

    snap1 = tracemalloc.take_snapshot()
    start_time = time.perf_counter()

    try:
        goal_node = algo(problem)
        status = "Solved" if goal_node else "Failed"
    except Exception:
        status = "Error"

    end_time = time.perf_counter()
    snap2 = tracemalloc.take_snapshot()

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # ---------------- MEMORY METRICS ----------------
    return_dict['status'] = status
    return_dict['time'] = end_time - start_time

    return_dict['mem_current_mb'] = current_mem / (1024 * 1024)
    return_dict['mem_peak_mb'] = peak_mem / (1024 * 1024)

    # ---------------- MEMORY BREAKDOWN ----------------
    top_stats = snap2.compare_to(snap1, 'lineno')

    return_dict['mem_top'] = [
        {
            "file": str(stat.traceback),
            "size_mb": stat.size_diff / (1024 * 1024)
        }
        for stat in top_stats[:10]
    ]


def main():
    algorithms = {
        "DFS (Tree)": depth_first_tree_search,
        "DFS (Graph)": depth_first_graph_search
    }

    stats = {
        name: {
            'times': [],
            'current_mem': [],
            'peak_mem': [],
            'solved': 0,
            'total': 0
        }
        for name in algorithms.keys()
    }

    timeout_seconds = 60

    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    print("\nStarting DFS Benchmark Suite...")

    for i in range(1, 10):
        filename = f"test{i:02d}.txt"

        if not os.path.exists(filename):
            print(f"\n[!] File {filename} not found. Skipping...")
            continue

        print(f"\nProcessing {filename}...")
        print("=" * 70)
        print(f"{'Algorithm':<15} | {'Status':<8} | {'Time (s)':<10} | {'Mem (MB)':<20}")
        print("-" * 70)

        with open(filename, 'r') as f:
            slitherlink.stdin = f
            board_template = Board.parse_instance()

        for name, algo in algorithms.items():
            fresh_board = copy.deepcopy(board_template)
            return_dict.clear()

            p = multiprocessing.Process(
                target=search_worker,
                args=(algo, fresh_board, return_dict)
            )

            p.start()
            p.join(timeout_seconds)

            stats[name]['total'] += 1

            if p.is_alive():
                p.terminate()
                p.join()

                status = "Timeout"
                time_taken = timeout_seconds

                stats[name]['times'].append(time_taken)

                print(f"{name:<15} | {status:<8} | {time_taken:<10.4f} | N/A")

            else:
                status = return_dict.get('status', 'Error')
                time_taken = return_dict.get('time', 0.0)

                current_mem = return_dict.get('mem_current_mb', 0.0)
                peak_mem = return_dict.get('mem_peak_mb', 0.0)

                stats[name]['times'].append(time_taken)
                stats[name]['current_mem'].append(current_mem)
                stats[name]['peak_mem'].append(peak_mem)

                if status == "Solved":
                    stats[name]['solved'] += 1

                print(f"{name:<15} | {status:<8} | {time_taken:<10.4f} | "
                      f"{current_mem:.2f} / {peak_mem:.2f}")

                # ---------------- MEMORY BREAKDOWN ----------------
                if 'mem_top' in return_dict:
                    print("   Top memory usage:")
                    for item in return_dict['mem_top'][:5]:
                        print(f"     {item['size_mb']:.3f} MB -> {item['file']}")

        print("=" * 70)

    # ---------------- FINAL SUMMARY ----------------
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"{'Algorithm':<15} | {'Solved':<8} | {'Avg Time':<10} | {'Current / Peak MB'}")
    print("-" * 70)

    for name, data in stats.items():
        total = data['total']
        if total == 0:
            continue

        solved_ratio = f"{data['solved']}/{total}"

        avg_time = sum(data['times']) / len(data['times']) if data['times'] else 0
        avg_current = sum(data['current_mem']) / len(data['current_mem']) if data['current_mem'] else 0
        avg_peak = sum(data['peak_mem']) / len(data['peak_mem']) if data['peak_mem'] else 0

        print(f"{name:<15} | {solved_ratio:<8} | {avg_time:<10.4f} | "
              f"{avg_current:.2f} / {avg_peak:.2f}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()