# Planeador de Rotas Multi-Objetivo para Transportes Públicos do Porto

##  Constituição do Grupo

- **PG60289** - Pedro Gomes
- **PG59800** - Tiago Moreira
- **PG60252** - Eduardo Vilaça
- **PG60285** - Nuno André Ni

##  Estrutura do Repositório
```
├── code
│   ├── constants.py
│   ├── graph_builder.py
│   ├── gtfs_loader.py
│   ├── main.py
│   ├── metro_porto
│   │   ├── agency.txt
│   │   ├── calendar.txt
│   │   ├── routes.txt
│   │   ├── shapes.txt
│   │   ├── stops.txt
│   │   ├── stop_times.txt
│   │   └── trips.txt
│   ├── optimizer.py
│   ├── __pycache__
│   │   ├── constants.cpython-312.pyc
│   │   ├── graph_builder.cpython-312.pyc
│   │   ├── gtfs_loader.cpython-312.pyc
│   │   ├── optimizer.cpython-312.pyc
│   │   └── visualizer.cpython-312.pyc
│   ├── stcp_porto
│   │   ├── agency.txt
│   │   ├── calendar_dates.txt
│   │   ├── calendar.txt
│   │   ├── routes.txt
│   │   ├── shapes.txt
│   │   ├── stops.txt
│   │   ├── stop_times.txt
│   │   ├── transfers.txt
│   │   └── trips.txt
│   └── visualizer.py
├── README.md
└── report
    ├── Apresentacao_CIN__Projeto_.pdf
    └── Relatorio_CIN.pdf
```
## Manual de Utilizador

### Pré-requisitos

```bash
pip install pandas networkx numpy matplotlib geopy scipy
```

### Correr
```bash
python3 main.py -d DIFICULDADE [facil,medio,dificil]
```

### Paramêtros Configuráveis -> constants.py

- **CO2_METRO_G_KM** - Gasto de CO₂ por Km percorrido de Metro
- **CO2_STCP_G_KM** - Gasto de CO₂ por Km percorrido de Autocarro
- **VELOCIDADE_PE_KMH** - Velocidade da pessoa a pé em Km/H
- **MAX_WALK_DIST_METERS** - Distância máxima a pé entre paragens
- **KCAL_PER_MIN** - Kcal queimadas por minuto a andar
- **N_SUBPROBLEMAS** - Tamanho da população
- **N_GERACOES** - Número de gerações do algoritmo
- **DIFICULDADE_PADRAO** - Dificuldade do cenário
- **PENALTY_PE** - Penalidade por andar mais de uma hora a pé em minutos
- **PENALTY_TRANSBORDO** - Penalidade por transbordo em minutos
