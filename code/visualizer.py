"""
Módulo para visualização de rotas e fronteiras de Pareto.
"""
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np
import random

from graph_builder import CO2_METRO_G_KM, CO2_STCP_G_KM, VELOCIDADE_PE_KMH
from constants import KCAL_PER_MIN


def plotar_pareto_front(solucoes_validas, origem, destino):
    """
    Plota a fronteira de Pareto das soluções.
    
    Args:
        solucoes_validas: Lista de dicionários com 'tempo' e 'co2'
        origem: Nó de origem
        destino: Nó de destino
    """
    if not solucoes_validas:
        print("Nenhuma solução válida encontrada para plotar.")
        return
    
    # Remover duplicados
    pontos_unicos = list(set([(s['tempo'], s['co2']) for s in solucoes_validas]))
    pontos_unicos.sort(key=lambda x: x[0])
    
    tempos = [p[0] for p in pontos_unicos]
    emissoes = [p[1] for p in pontos_unicos]

    # Desenhar Gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(tempos, emissoes, 'o-', color='green', markersize=8, linewidth=2, label='Fronteira de Pareto')
    
    # Anotar os pontos
    for t, c in pontos_unicos:
        plt.annotate(f"{t:.0f}m | {c:.0f}g", 
                     (t, c), 
                     textcoords="offset points", 
                     xytext=(0,10), 
                     ha='center',
                     fontsize=8)

    plt.title(f"Compromisso Tempo vs Sustentabilidade\n({origem} -> {destino})")
    plt.xlabel("Tempo de Viagem (minutos)")
    plt.ylabel("Emissões CO2 (gramas)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.show()


def imprimir_itinerario(G, path, stop_names_dict):
    """
    Imprime o itinerário detalhado de um caminho.
    
    Args:
        G: Grafo de transportes
        path: Lista de nós representando o caminho
        stop_names_dict: Dicionário com nomes das paragens
    """
    if not path or len(path) < 2:
        print("Caminho vazio ou inválido.")
        return

    # Construir Segmentos (Agrupar paragens do mesmo transporte)
    segmentos = []
    
    # Inicializar primeiro segmento
    u, v = path[0], path[1]
    edge_data = min(G.get_edge_data(u, v).values(), key=lambda x: x['weight'])
    
    current_segment = {
        'mode': edge_data['mode'],
        'trip_id': edge_data.get('trip_id'),
        'start_node': u,
        'end_node': v,
        'stops': [u, v],
        'total_time': edge_data['weight'],
        'total_co2': edge_data['co2']
    }
    
    # Iterar pelo resto do caminho
    for i in range(1, len(path) - 1):
        u, v = path[i], path[i+1]
        edge_data = min(G.get_edge_data(u, v).values(), key=lambda x: x['weight'])
        
        mode = edge_data['mode']
        trip = edge_data.get('trip_id')
        
        # Lógica de Agrupamento: Mesmo modo e mesma viagem?
        mesmo_modo = (mode == current_segment['mode'])
        mesma_viagem = (trip == current_segment['trip_id'])
        
        if mesmo_modo and mesma_viagem:
            # Continuar segmento atual
            current_segment['end_node'] = v
            current_segment['stops'].append(v)
            current_segment['total_time'] += edge_data['weight']
            current_segment['total_co2'] += edge_data['co2']
        else:
            # Fechar segmento anterior e iniciar novo
            segmentos.append(current_segment)
            
            current_segment = {
                'mode': mode,
                'trip_id': trip,
                'start_node': u,
                'end_node': v,
                'stops': [u, v],
                'total_time': edge_data['weight'],
                'total_co2': edge_data['co2']
            }
            
    # Adicionar o último segmento pendente
    segmentos.append(current_segment)

    # Imprimir Visualmente
    total_t = sum(s['total_time'] for s in segmentos)
    total_c = sum(s['total_co2'] for s in segmentos)
    
    print("-" * 60)
    print(f" DURAÇÃO: {total_t:.0f} min | EMISSÕES: {total_c:.0f} gCO2")
    print("-" * 60)
    
    for i, seg in enumerate(segmentos):
        start_name = stop_names_dict.get(seg['start_node'], seg['start_node'])
        end_name = stop_names_dict.get(seg['end_node'], seg['end_node'])
        n_stops = len(seg['stops']) - 1
        
        # Estilização por modo
        if seg['mode'] == 'metro':
            icon = "METRO"
            detalhe = f"Linha {seg['trip_id']}"
        elif seg['mode'] == 'stcp':
            icon = "AUTOCARRO"
            # Tenta limpar o trip_id para mostrar só o nº da rota
            rota = str(seg['trip_id']).split('_')[0] 
            detalhe = f"Rota {rota}"
        else:
            icon = "A PÉ"
            detalhe = "Caminhada"
            
        print(f"{icon} ({seg['total_time']:.1f} min)")
        print(f"    {start_name}")
        print(f"    {end_name}")
        
        if seg['mode'] != 'walk':
            print(f"      ({n_stops} paragens - {detalhe})")
        
        if i < len(segmentos) - 1:
            print("\n ---TRANSBORDO---\n")
            
    print("-" * 60)


def mostrar_todas_opcoes(G, solucoes_validas, stop_names_dict):
    """
    Mostra todas as opções de rota encontradas.
    
    Args:
        G: Grafo de transportes
        solucoes_validas: Lista de dicionários com soluções
        stop_names_dict: Dicionário com nomes das paragens
    """
    if not solucoes_validas:
        print("Nenhuma solução válida encontrada.")
        return
    
    print("\n" + "="*60)
    print(" RESULTADOS DO PLANEADOR DE ROTAS")
    print("="*60 + "\n")
    
    for i, sol in enumerate(solucoes_validas):
        # Lógica de Rótulos (Rápido / Ecológico / Fitness)
        if i == 0:
            tag = "MAIS RÁPIDA"
        elif sol['co2'] == min(s['co2'] for s in solucoes_validas):
            tag = "MAIS ECOLÓGICA"
        elif sol['exercicio'] > 15:
            tag = "OPÇÃO FITNESS"
        else:
            tag = "️EQUILIBRADA"
            
        print(f"{tag}")
        print(f"Tempo: {sol['tempo']:.1f} min |  CO2: {sol['co2']:.1f} g")
        print(f"Exercício: {sol['exercicio']:.1f} min a pé (~{sol['calorias']:.0f} kcal queimadas)")
        print()
        
        imprimir_itinerario(G, sol['path'], stop_names_dict)
        print("\n" + "="*60)


def visualizar_grafo_rotas(G, solucoes_validas, stop_names_dict):
    """
    Visualiza todas as rotas num grafo esquematizado.
    
    Args:
        G: Grafo de transportes
        solucoes_validas: Lista de soluções
        stop_names_dict: Dicionário com nomes das paragens
    """
    S = nx.MultiDiGraph()
    
    num_rotas = len(solucoes_validas)
    if num_rotas == 0:
        print("Nenhuma rota para visualizar.")
        return
        
    print(f"\nA gerar esquema gráfico para {num_rotas} rotas...")
    
    hues = np.linspace(0, 1, num_rotas, endpoint=False)
    cores_unicas = [mcolors.hsv_to_rgb((h, 1.0, 0.90)) for h in hues]
    random.Random(42).shuffle(cores_unicas)
    
    # Dicionário para guardar info da aresta: (u, v, key) -> texto
    labels_detalhadas = {}
    
    # Para guardar totais de fitness para a legenda
    fitness_por_rota = [] 

    for i, sol in enumerate(solucoes_validas):
        path = sol['path']
        cor_rota = cores_unicas[i]
        
        if len(path) < 2: 
            fitness_por_rota.append((0, 0))
            continue
        
        # Variáveis acumuladoras da rota inteira
        total_walk_time_rota = 0
        
        curr_segment_start = path[0]
        edge_first = min(G.get_edge_data(path[0], path[1]).values(), key=lambda x: x['weight'])
        curr_mode = edge_first['mode']
        curr_trip = edge_first.get('trip_id')
        curr_time = 0
        curr_dist = 0.0
        
        for k in range(len(path) - 1):
            u, v = path[k], path[k+1]
            data = min(G.get_edge_data(u, v).values(), key=lambda x: x['weight'])
            
            # Acumular tempo a pé global da rota
            if data['mode'] == 'walk':
                total_walk_time_rota += data['weight']
            
            mudou_modo = (data['mode'] != curr_mode)
            mudou_viagem = (data.get('trip_id') != curr_trip)
            
            # Se mudou de transporte (segmentação)
            if (mudou_modo or mudou_viagem) and not (curr_mode == 'walk' and data['mode'] == 'walk'):
                # --- FECHAR SEGMENTO ANTERIOR ---
                label_start = stop_names_dict.get(curr_segment_start, curr_segment_start)
                label_u = stop_names_dict.get(u, u)
                
                S.add_node(curr_segment_start, label=label_start)
                S.add_node(u, label=label_u)
                
                # Definir texto da etiqueta (Label)
                if curr_mode == 'walk':
                    kcal_seg = curr_time * KCAL_PER_MIN
                    info_label = f"A PÉ\n{curr_time:.0f}m | {kcal_seg:.0f}kcal"
                else:
                    info_label = f"{curr_mode.upper()}\n{curr_time:.0f} m | {curr_dist:.1f}km"
                
                key = S.add_edge(curr_segment_start, u, color=cor_rota, weight=curr_time)
                labels_detalhadas[(curr_segment_start, u, key)] = info_label
                
                # --- INICIAR NOVO SEGMENTO ---
                curr_segment_start = u
                curr_mode = data['mode']
                curr_trip = data.get('trip_id')
                curr_time = 0
                curr_dist = 0.0
            
            # Acumular valores do segmento atual
            curr_time += data['weight']
            
            # Distância do segmento
            dist_seg = 0
            if data['mode'] == 'walk':
                dist_seg = (data['weight'] / 60) * VELOCIDADE_PE_KMH
            elif data['mode'] == 'metro':
                dist_seg = data['co2'] / CO2_METRO_G_KM if data['co2'] > 0 else 0
            elif data['mode'] == 'stcp':
                dist_seg = data['co2'] / CO2_STCP_G_KM if data['co2'] > 0 else 0
            curr_dist += dist_seg
            
        # --- FECHAR O ÚLTIMO SEGMENTO ---
        v_final = path[-1]
        label_final = stop_names_dict.get(v_final, v_final)
        S.add_node(curr_segment_start, label=stop_names_dict.get(curr_segment_start, curr_segment_start))
        S.add_node(v_final, label=label_final)
        
        if curr_mode == 'walk':
            kcal_seg = curr_time * KCAL_PER_MIN
            info_label = f"A PÉ\n{curr_time:.0f}m | {kcal_seg:.0f}kcal"
        else:
            info_label = f"{curr_mode.upper()}\n{curr_time:.0f} m | {curr_dist:.1f}km"
            
        key = S.add_edge(curr_segment_start, v_final, color=cor_rota, weight=curr_time)
        labels_detalhadas[(curr_segment_start, v_final, key)] = info_label
        
        # Guardar totais para a legenda
        fitness_por_rota.append((total_walk_time_rota, total_walk_time_rota * KCAL_PER_MIN))

    # --- DESENHO ---
    plt.figure(figsize=(18, 12))
    pos = nx.spring_layout(S, k=3, seed=42)
    
    # Nós
    node_colors = []
    global_orig = solucoes_validas[0]['path'][0]
    global_dest = solucoes_validas[0]['path'][-1]
    for n in S.nodes():
        if n == global_orig:
            node_colors.append('#00FF00')
        elif n == global_dest:
            node_colors.append('#FF0000')
        else:
            node_colors.append('#DDDDDD')

    nx.draw_networkx_nodes(S, pos, node_color=node_colors, node_size=700, edgecolors='black')
    
    # Labels Nós
    node_lbls = nx.get_node_attributes(S, 'label')
    short_lbls = {k: v.split('(')[0][:15] for k, v in node_lbls.items()}
    nx.draw_networkx_labels(S, pos, labels=short_lbls, font_size=10, font_weight='bold')

    # Arestas e Labels
    for u, v, key, d in S.edges(data=True, keys=True):
        c = d['color']
        rad = 0.1 + (key * 0.15)
        nx.draw_networkx_edges(S, pos, edgelist=[(u, v)], edge_color=[c], 
                               connectionstyle=f'arc3, rad={rad}', width=2, arrowsize=15)
        
        lbl_txt = labels_detalhadas.get((u, v, key), "")
        
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx = x2 - x1
        dy = y2 - y1
        dist = np.sqrt(dx**2 + dy**2)
        if dist > 0:
            nx_vec = dy / dist
            ny_vec = -dx / dist
            sagitta = (rad * dist) / 2
            lbl_x = mx + (nx_vec * sagitta)
            lbl_y = my + (ny_vec * sagitta)
        else:
             lbl_x, lbl_y = mx, my
        plt.text(lbl_x, lbl_y, lbl_txt,
                 fontsize=10, color='black', ha='center', va='center',
                 bbox=dict(facecolor='white', alpha=0.9, edgecolor=c, boxstyle='round,pad=0.2', linewidth=1.5))

    # --- LEGENDA ---
    from matplotlib.lines import Line2D
    legend_elements = []
    for i in range(num_rotas):
        t = solucoes_validas[i]['tempo']
        c = solucoes_validas[i]['co2']
        w_time, w_kcal = fitness_por_rota[i]
        
        # Formato: Opção 1: 30min | 500g (10m | 40kcal)
        lbl = f"Opção {i+1}: {t:.0f}min | {c:.0f}gCO2\nA Pé ({w_time:.0f}m | {w_kcal:.0f}kcal)"
        
        legend_elements.append(Line2D([0], [0], color=cores_unicas[i], lw=3, label=lbl))

    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), title="Rotas")
    plt.title("Esquema de Rotas")
    plt.axis('off')
    plt.tight_layout()
    plt.show()
