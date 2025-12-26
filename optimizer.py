"""
Módulo para otimização multi-objetivo (MOEA/D) de rotas de transporte.
"""
import networkx as nx
import random
from graph_builder import avaliar_caminho


N_SUBPROBLEMAS = 40  # Tamanho da população do MOEA/D


def gerar_pesos_dijkstra(G, origem, destino, w_tempo, w_co2):
    """
    Executa Dijkstra modificado com pesos customizados.
    
    Args:
        G: Grafo de transportes
        origem: Nó de origem
        destino: Nó de destino
        w_tempo: Peso para o tempo
        w_co2: Peso para CO2
        
    Returns:
        list: Caminho encontrado ou None
    """
    try:
        def weight_fn(u, v, d):
            # Se d tiver múltiplas chaves (MultiGraph), iteramos para achar o mínimo
            if 'weight' not in d: 
                min_cost = float('inf')
                for k, attrs in d.items():
                    cost = w_tempo * attrs.get('weight', 1e6) + w_co2 * (attrs.get('co2', 0) / 20.0)
                    if attrs.get('mode') == 'walk':
                        cost *= 1.5
                    if cost < min_cost:
                        min_cost = cost
                return min_cost
            else:
                # Caso simples
                cost = w_tempo * d.get('weight', 1e6) + w_co2 * (d.get('co2', 0) / 20.0)
                if d.get('mode') == 'walk':
                    cost *= 1.5
                return cost
            
        return nx.dijkstra_path(G, origem, destino, weight=weight_fn)
    except:
        return None


def mutacao(G, path):
    """
    Tenta criar um desvio aleatório no caminho.
    
    Args:
        G: Grafo de transportes
        path: Caminho atual
        
    Returns:
        list: Caminho mutado ou original se falhar
    """
    if random.random() > 0.4 or len(path) < 5:
        return path
    
    idx_a = random.randint(0, len(path) - 4)
    idx_b = random.randint(idx_a + 2, len(path) - 1)
    
    try:
        # Tenta conectar A e B pelo caminho mais curto simples (ignora pesos complexos)
        short = nx.shortest_path(G, path[idx_a], path[idx_b], weight='weight')
        return path[:idx_a] + short + path[idx_b+1:]
    except:
        return path


def otimizar_moead(G, origem, destino, geracoes=100, n_subproblemas=N_SUBPROBLEMAS):
    """
    Executa o algoritmo MOEA/D para otimização multi-objetivo.
    
    Args:
        G: Grafo de transportes
        origem: Nó de origem
        destino: Nó de destino
        geracoes: Número de gerações
        n_subproblemas: Tamanho da população
        
    Returns:
        tuple: (população_final, lista_de_pesos)
    """
    print("\n--- INICIANDO OTIMIZAÇÃO MOEA/D ---")
    
    # Inicialização da População (Dijkstra com vários pesos)
    populacao = []
    pesos = []
    
    for i in range(n_subproblemas):
        w_t = i / (n_subproblemas - 1)  # 0.0 a 1.0
        w_c = 1.0 - w_t
        pesos.append((w_t, w_c))
        
        # Gerar solução inicial inteligente
        caminho = gerar_pesos_dijkstra(G, origem, destino, w_t, w_c)
        if caminho:
            populacao.append(caminho)
        else:
            # Se falhar, tenta o caminho mais rápido puro
            try:
                populacao.append(nx.shortest_path(G, origem, destino, weight='weight'))
            except:
                pass

    print(f"População inicial: {len(populacao)} soluções.")

    # Ciclo Evolutivo Simplificado
    for gen in range(geracoes):
        for i in range(len(populacao)):
            # Mutação simples na solução atual
            filho = mutacao(G, populacao[i])
            
            # Avaliar
            f_tempo_filho, f_co2_filho = avaliar_caminho(G, filho)
            f_tempo_pai, f_co2_pai = avaliar_caminho(G, populacao[i])
            
            # Decisão Tchebycheff simplificada (usando pesos do subproblema i)
            w_t, w_c = pesos[i]
            
            # Normalização implícita (Tempo ~60, CO2 ~1000 -> CO2 vale 16x menos na soma direta)
            custo_filho = w_t * f_tempo_filho + w_c * (f_co2_filho / 20.0)
            custo_pai = w_t * f_tempo_pai + w_c * (f_co2_pai / 20.0)
            
            if custo_filho < custo_pai:
                populacao[i] = filho

        if gen % 20 == 0:
            print(f"Geração {gen}/{geracoes} completada.")

    print(f"Otimização concluída após {geracoes} gerações.")
    return populacao, pesos


def extrair_solucoes_validas(G, populacao):
    """
    Filtra e retorna soluções válidas da população.
    
    Args:
        G: Grafo de transportes
        populacao: Lista de caminhos
        
    Returns:
        list: Lista de dicionários com 'tempo', 'co2' e 'path'
    """
    solucoes_validas = []
    custos_vistos = set()
    
    for path in populacao:
        t, c = avaliar_caminho(G, path)
        
        # Se o tempo for > 400, sabemos que levou penalização (é inválido)
        if t < 400 and (int(t), int(c)) not in custos_vistos:
            # Calcular tempo a pé
            t_pe = 0
            for k in range(len(path)-1):
                d = min(G.get_edge_data(path[k], path[k+1]).values(), key=lambda x: x['weight'])
                if d['mode'] == 'walk':
                    t_pe += d['weight']
            
            calorias = t_pe * 4  # Estimativa: 4 kcal/min a andar
            
            solucoes_validas.append({
                'tempo': t, 
                'co2': c, 
                'path': path, 
                'exercicio': t_pe, 
                'calorias': calorias
            })
            custos_vistos.add((int(t), int(c)))
    
    solucoes_validas.sort(key=lambda x: x['tempo'])
    return solucoes_validas
