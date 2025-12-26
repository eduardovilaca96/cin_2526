"""
Planeador de Rotas Multi-Objetivo para Transportes Públicos do Porto
Utilizando MOEA/D para otimizar tempo de viagem e emissões de CO2
"""
import matplotlib
matplotlib.use('TkAgg')

from gtfs_loader import load_gtfs_data
from graph_builder import build_transport_graph, gerar_cenario_random_walk, criar_mapa_nomes
from optimizer import otimizar_moead, extrair_solucoes_validas
from visualizer import plotar_pareto_front, mostrar_todas_opcoes, visualizar_grafo_rotas


def main():
    """Função principal do planeador de rotas."""
    
    print("="*60)
    print("PLANEADOR DE ROTAS MULTI-OBJETIVO - PORTO")
    print("="*60)
    
    # 1. CARREGAR DADOS GTFS
    print("\nFase 1: Carregamento de Dados GTFS")
    print("-" * 60)
    s_metro, t_metro, trips_m = load_gtfs_data("metro_porto", "metro")
    s_stcp, t_stcp, trips_s = load_gtfs_data("stcp_porto", "stcp", service_filter="UTEIS")
    
    if s_metro is None or s_stcp is None:
        print("\n Erro ao carregar dados GTFS. Verifique as pastas metro_porto e stcp_porto.")
        return
    
    # 2. CRIAR GRAFO DE TRANSPORTES
    print("\n️Fase 2: Construção do Grafo Multimodal")
    print("-" * 60)
    G = build_transport_graph(s_metro, t_metro, s_stcp, t_stcp)
    print(f" Grafo criado com {G.number_of_nodes()} nós e {G.number_of_edges()} arestas.")
    
    # 3. CRIAR MAPA DE NOMES
    stop_names_dict = criar_mapa_nomes(s_metro, s_stcp)
    
    # 4. GERAR CENÁRIO (ORIGEM E DESTINO)
    print("\nFase 3: Geração de Cenário")
    print("-" * 60)
    origem, destino = gerar_cenario_random_walk(G, dificuldade='dificil')
    print(f"Origem: {stop_names_dict.get(origem, origem)}")
    print(f"Destino: {stop_names_dict.get(destino, destino)}")
    
    # 5. OTIMIZAÇÃO MOEA/D
    print("\nFase 4: Otimização Multi-Objetivo (MOEA/D)")
    print("-" * 60)
    populacao, pesos = otimizar_moead(G, origem, destino, geracoes=100)
    
    # 6. EXTRAIR SOLUÇÕES VÁLIDAS
    print("\nFase 5: Extração de Soluções Válidas")
    print("-" * 60)
    solucoes_validas = extrair_solucoes_validas(G, populacao)
    print(f"Encontradas {len(solucoes_validas)} soluções válidas (Pareto front).")
    
    # 7. MOSTRAR RESULTADOS NA CONSOLA
    mostrar_todas_opcoes(G, solucoes_validas, stop_names_dict)
    
    # 8. VISUALIZAÇÃO - FRONTEIRA DE PARETO
    print("\nFase 6: Visualização da Fronteira de Pareto")
    print("-" * 60)
    print("A gerar gráfico da fronteira de Pareto...")
    plotar_pareto_front(solucoes_validas, 
                       stop_names_dict.get(origem, origem),
                       stop_names_dict.get(destino, destino))
    
    # 9. VISUALIZAÇÃO - GRAFO DE ROTAS
    print("\n️Fase 7: Visualização do Grafo de Rotas")
    print("-" * 60)
    visualizar_grafo_rotas(G, solucoes_validas, stop_names_dict)
    
    print("\n" + "="*60)
    print("PLANEAMENTO CONCLUÍDO COM SUCESSO!")
    print("="*60)


if __name__ == "__main__":
    main()
