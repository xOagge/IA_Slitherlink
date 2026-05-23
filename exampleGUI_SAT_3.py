# exampleGUI_SAT_3.py - Versão final que funciona
#!/usr/bin/env python3

import sys
import tkinter as tk
from slitherlink_SAT_3 import Board, Slitherlink
from slitherlink_gui import SlitherlinkGUI
from search import depth_first_graph_search, astar_search
import time

def main():
    # Ler tabuleiro do stdin
    board = Board.parse_instance()
    board_list = board.get_board()
    
    # Imprimir para stderr (não interfere com o output da solução)
    sys.stderr.write(f"Tabuleiro carregado: {board.rows}x{board.cols}\n")
    sys.stderr.write("Iniciando busca DFS...\n")
    sys.stderr.flush()
    
    start_time = time.perf_counter()
    
    # Criar problema
    problem = Slitherlink(board)
    
    # Usar DFS que é completo
    goal_node = depth_first_graph_search(problem)
    
    # Se DFS falhar, tentar A*
    if not goal_node:
        sys.stderr.write("DFS não encontrou solução, tentando A*...\n")
        goal_node = astar_search(problem)
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    if goal_node:
        if problem.goal_test(goal_node.state):
            sys.stderr.write(f"\n✓ SOLUÇÃO VÁLIDA encontrada em {elapsed:.2f} segundos!\n")
            
            # IMPRIMIR SOLUÇÃO PARA STDOUT
            solution_str = goal_node.state.board.print()
            print(solution_str)
            
            # Estatísticas
            active_edges = len(goal_node.state.board.all_drawn_edges)
            sys.stderr.write(f"Total de arestas ativas: {active_edges}\n")
            sys.stderr.write(f"Profundidade da solução: {goal_node.depth}\n")
            
            # Mostrar GUI
            sys.stderr.write("\nAbrindo interface gráfica...\n")
            root = tk.Tk()
            app = SlitherlinkGUI(root, board_list)
            
            # Carregar solução na GUI
            sol_grid = [line.split('\t') for line in solution_str.split('\n') if line.strip()]
            app.load_solution(sol_grid)
            
            root.title(f"Slitherlink - Solução {board.rows}x{board.cols} ({elapsed:.2f}s)")
            root.mainloop()
            
            sys.exit(0)
        else:
            sys.stderr.write(f"ERRO: Solução encontrada mas é INVÁLIDA!\n")
            sys.exit(1)
    else:
        sys.stderr.write(f"ERRO: Nenhuma solução encontrada após {elapsed:.2f} segundos!\n")
        sys.exit(1)

if __name__ == "__main__":
    main()