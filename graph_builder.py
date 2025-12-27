"""
Módulo para construção e manipulação do grafo de transportes multimodal.
"""
import networkx as nx
import random
from geopy.distance import geodesic
from scipy.spatial import cKDTree
import pandas as pd

from constants import (
    CO2_METRO_G_KM,
    CO2_STCP_G_KM,
    VELOCIDADE_PE_KMH,
    MAX_WALK_DIST_METERS,
    PENALTY_PE
)


def build_transport_graph(stops_metro, stimes_metro, stops_stcp, stimes_stcp):
    """
    Constrói um grafo multimodal de transportes públicos.
    
    Args:
        stops_metro: DataFrame com paragens do metro
        stimes_metro: DataFrame com horários do metro
        stops_stcp: DataFrame com paragens do STCP
        stimes_stcp: DataFrame com horários do STCP
        
    Returns:
        nx.MultiDiGraph: Grafo com todas as conexões de transporte
    """
    G = nx.MultiDiGraph()
    
    # --- 1. ARESTAS DE TRANSPORTE ---
    def add_edges(stops_df, stimes_df, mode, co2_rate):
        if stops_df is None or stimes_df is None:
            return
        
        coords = stops_df.set_index('stop_id')[['stop_lat', 'stop_lon']].to_dict('index')
        trips = stimes_df.sort_values(['trip_id', 'stop_sequence']).groupby('trip_id')
        
        count = 0
        for trip_id, group in trips:
            stops_seq = group.to_dict('records')
            for i in range(len(stops_seq) - 1):
                u, v = stops_seq[i], stops_seq[i+1]
                u_id, v_id = u['stop_id'], v['stop_id']
                
                try:
                    # Tempo
                    duracao = (v['arrival_sec'] - u['departure_sec']) / 60
                    if duracao < 0:
                        duracao += 24*60
                    if duracao < 0.1:
                        duracao = 0.5
                    
                    # Distância e CO2
                    c_u = (coords[u_id]['stop_lat'], coords[u_id]['stop_lon'])
                    c_v = (coords[v_id]['stop_lat'], coords[v_id]['stop_lon'])
                    dist_km = geodesic(c_u, c_v).km
                    
                    G.add_edge(u_id, v_id, 
                               weight=duracao, 
                               co2=dist_km * co2_rate, 
                               mode=mode, 
                               trip_id=trip_id)
                    count += 1
                except KeyError:
                    continue
        print(f"Adicionadas {count} arestas de {mode}.")

    add_edges(stops_metro, stimes_metro, 'metro', CO2_METRO_G_KM)
    add_edges(stops_stcp, stimes_stcp, 'stcp', CO2_STCP_G_KM)
    
    # --- 2. ARESTAS A PÉ (KDTree) ---
    print("Calculando ligações a pé...")
    all_stops = pd.concat([stops_metro, stops_stcp]).reset_index(drop=True)
    coords_np = all_stops[['stop_lat', 'stop_lon']].values
    
    tree = cKDTree(coords_np)
    pairs = tree.query_pairs(r=0.004)  # ~400m raio grosseiro
    
    walk_count = 0
    for i, j in pairs:
        s1 = all_stops.iloc[i]
        s2 = all_stops.iloc[j]
        
        dist = geodesic((s1['stop_lat'], s1['stop_lon']), 
                        (s2['stop_lat'], s2['stop_lon'])).meters
        
        if dist <= MAX_WALK_DIST_METERS:
            t_walk = (dist / 1000) / VELOCIDADE_PE_KMH * 60
            # Adicionar ida e volta
            G.add_edge(s1['stop_id'], s2['stop_id'], weight=t_walk, co2=0, mode='walk', trip_id='walk')
            G.add_edge(s2['stop_id'], s1['stop_id'], weight=t_walk, co2=0, mode='walk', trip_id='walk')
            walk_count += 2
            
    print(f"Adicionadas {walk_count} arestas a pé.")
    return G


def gerar_cenario_random_walk(G, dificuldade):
    """
    Gera origem e destino garantindo conectividade através de um passeio aleatório.
    
    Args:
        G: Grafo de transportes
        dificuldade: 'facil', 'medio' ou 'dificil'
        
    Returns:
        tuple: (origem, destino)
    """
    # Definir número de passos baseado na dificuldade
    if dificuldade == 'facil':
        steps = random.randint(15, 50)      # Viagem curta"
    elif dificuldade == 'medio':
        steps = random.randint(50, 100)     # Viagem média
    elif dificuldade == 'dificil':
        steps = random.randint(100, 200)
    else:
        steps = 20

    # 1. Escolher origem válida (que tenha vizinhos)
    nodes = list(G.nodes())
    start_node = random.choice(nodes)
    while not list(G.neighbors(start_node)):
        start_node = random.choice(nodes)
        
    # 2. Caminhar no grafo (Random Walk)
    curr = start_node
    path_taken = [curr]
    
    for _ in range(steps):
        neighbors = list(G.neighbors(curr))
        if not neighbors:
            break  # Beco sem saída
        curr = random.choice(neighbors)
        path_taken.append(curr)
        
    end_node = curr
    
    # 3. Garantir que origem != destino
    if start_node == end_node:
        return gerar_cenario_random_walk(G, dificuldade)
        
    print(f"Cenário '{dificuldade}' gerado: {steps} passos de distância no grafo.")
    return start_node, end_node


def avaliar_caminho(G, path):
    """
    Calcula Tempo e CO2 de um caminho com penalizações.
    
    Args:
        G: Grafo de transportes
        path: Lista de nós representando o caminho
        
    Returns:
        tuple: (tempo_total, co2_total)
    """
    tempo, co2, t_pe, transbordos = 0, 0, 0, 0
    last_trip = None
    
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        # Pega a melhor aresta disponível
        edges = G.get_edge_data(u, v)
        if not edges:
            return 1e6, 1e6
        
        best = min(edges.values(), key=lambda x: x['weight'])
        
        tempo += best['weight']
        co2 += best['co2']
        
        if best['mode'] == 'walk':
            t_pe += best['weight']
        elif last_trip and best['trip_id'] != last_trip:
            transbordos += 1
            last_trip = best['trip_id']
        else:
            last_trip = best['trip_id']
            
    penalidade = 0
    if t_pe > 60:
        penalidade += PENALTY_PE
    
    return tempo + (transbordos*5) + penalidade, co2 + penalidade


def criar_mapa_nomes(stops_metro, stops_stcp):
    """
    Cria um dicionário para traduzir IDs em nomes de paragens.
    
    Args:
        stops_metro: DataFrame com paragens do metro
        stops_stcp: DataFrame com paragens do STCP
        
    Returns:
        dict: Mapeamento de stop_id para nome legível
    """
    nomes = {}
    
    # Processar Metro
    if stops_metro is not None:
        for _, row in stops_metro.iterrows():
            nome_limpo = row['stop_name'].replace('"', '').title()
            nomes[row['stop_id']] = f"{nome_limpo} (Metro)"
            
    # Processar STCP
    if stops_stcp is not None:
        for _, row in stops_stcp.iterrows():
            nome_limpo = row['stop_name'].replace('"', '').title()
            nomes[row['stop_id']] = f"{nome_limpo} (STCP)"
            
    return nomes
