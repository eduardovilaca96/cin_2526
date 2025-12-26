"""
Módulo para carregamento de dados GTFS (General Transit Feed Specification).
"""
import pandas as pd


def parse_gtfs_time(time_str):
    """
    Converte hora GTFS (ex: 25:30:00) para segundos desde meia-noite.
    
    Args:
        time_str: String no formato HH:MM:SS
        
    Returns:
        int: Segundos desde meia-noite, ou None se inválido
    """
    if pd.isna(time_str):
        return None
    try:
        parts = list(map(int, time_str.split(':')))
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except:
        return None


def load_gtfs_data(folder, prefix, service_filter=None):
    """
    Carrega dados GTFS de uma pasta específica.
    
    Args:
        folder: Caminho da pasta com ficheiros GTFS
        prefix: Prefixo para identificar o operador (ex: "metro", "stcp")
        service_filter: ID do serviço para filtrar (ex: "UTEIS")
        
    Returns:
        tuple: (stops_df, stop_times_df, trips_df) ou (None, None, None) em caso de erro
    """
    print(f"--- Carregando {prefix.upper()} ---")
    
    # 1. Carregar Paragens
    try:
        stops = pd.read_csv(f"{folder}/stops.txt")
        stops['stop_id'] = prefix + "_" + stops['stop_id'].astype(str)
    except FileNotFoundError:
        print(f"Erro: Ficheiro stops.txt não encontrado na pasta {folder}")
        return None, None, None

    # 2. Carregar Viagens (Trips)
    try:
        trips = pd.read_csv(f"{folder}/trips.txt")
        if service_filter and 'service_id' in trips.columns:
            trips = trips[trips['service_id'] == service_filter]
    except FileNotFoundError:
        print(f"Erro: trips.txt não encontrado.")
        return None, None, None

    # 3. Carregar Horários (Stop Times)
    try:
        stop_times = pd.read_csv(f"{folder}/stop_times.txt")
        # Filtrar apenas stop_times das trips válidas
        stop_times = stop_times[stop_times['trip_id'].isin(trips['trip_id'])]
        stop_times['stop_id'] = prefix + "_" + stop_times['stop_id'].astype(str)
        
        # Converter tempos (Crítico para performance)
        stop_times['arrival_sec'] = stop_times['arrival_time'].apply(parse_gtfs_time)
        stop_times['departure_sec'] = stop_times['departure_time'].apply(parse_gtfs_time)
        
        # Limpar nulos
        stop_times = stop_times.dropna(subset=['arrival_sec', 'departure_sec'])
    except FileNotFoundError:
        print(f"Erro: stop_times.txt não encontrado.")
        return None, None, None
    
    print(f"Carregados {len(stops)} paragens e {len(trips)} viagens.")
    return stops, stop_times, trips
