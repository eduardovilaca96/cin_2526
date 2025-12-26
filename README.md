# Planeador de Rotas Multi-Objetivo para Transportes Públicos do Porto

##  Constituição do Grupo

- **PG60289** - Pedro Gomes
- **PG59800** - Tiago Moreira
- **PG60252** - Eduardo Vilaça
- **PG60285** - Nuno André Ni

---

##  Descrição do Projeto

Sistema de planeamento de rotas multi-objetivo para a rede de transportes públicos do Porto (Metro e STCP), utilizando o algoritmo evolutivo **MOEA/D** (Multi-Objective Evolutionary Algorithm based on Decomposition) para otimizar simultaneamente:

-  **Tempo de viagem**
-  **Emissões de CO2**
-  **Exercício físico** (calorias queimadas ao caminhar)

O sistema gera uma **fronteira de Pareto** com múltiplas soluções de compromisso, permitindo ao utilizador escolher entre rotas mais rápidas, mais ecológicas ou mais equilibradas.

---

##  Estrutura do Repositório
```
projeto/
│
├── README.md                    
├── main.py                      
├── gtfs_loader.py              
├── graph_builder.py            
├── optimizer.py                
├── visualizer.py               
├── metro_porto/                
│   ├── agency.txt
│   ├── calendar.txt
│   ├── routes.txt
│   ├── shapes.txt
│   ├── stop_times.txt
│   ├── stops.txt
│   └── trips.txt
├── stcp_porto/                 
    ├── agency.txt
    ├── calendar_dates.txt
    ├── calendar.txt
    ├── routes.txt
    ├── shapes.txt
    ├── stop_times.txt
    ├── stops.txt
    ├── transfers.txt
    └── trips.txt
```

---

##  Como Executar

### Pré-requisitos

```bash
pip install pandas networkx numpy matplotlib geopy scipy
```

### Execução

```bash
python3 main.py
```

---

##  Funcionalidades

### 1. **Carregamento de Dados**
- Lê ficheiros GTFS (General Transit Feed Specification) do Metro e STCP
- Processa horários, paragens e viagens
- Filtra serviços (ex: dias úteis)

### 2. **Construção do Grafo Multimodal**
- **Arestas de transporte**: Metro e STCP com tempos e emissões reais
- **Arestas a pé**: Conexões entre paragens próximas (≤300m) usando KDTree
- **MultiDiGraph**: Permite múltiplas conexões entre nós

### 3. **Otimização Multi-Objetivo (MOEA/D)**
- População inicial gerada com Dijkstra ponderado
- 40 subproblemas com pesos diferentes (tempo vs CO2)
- 100 gerações com mutação inteligente
- Produz fronteira de Pareto com soluções de compromisso

### 4. **Visualizações**

####  Consola
- Itinerários detalhados com ícones ( Metro,  Autocarro,  A pé)
- Tempo total, emissões de CO2 e calorias queimadas
- Classificação automática: Mais Rápida , Mais Ecológica , Fitness 

####  Gráficos
- **Fronteira de Pareto**: Trade-off tempo vs emissões
- **Grafo de Rotas**: Visualização esquemática de todas as rotas com transbordos

---

## ️ Parâmetros Configuráveis

### `graph_builder.py`
```python
CO2_METRO_G_KM = 40.0          # Emissões do metro (g/km)
CO2_STCP_G_KM = 109.9          # Emissões dos autocarros (g/km)
VELOCIDADE_PE_KMH = 5.0        # Velocidade de caminhada (km/h)
MAX_WALK_DIST_METERS = 300     # Distância máxima a pé entre paragens
```

### `optimizer.py`
```python
N_SUBPROBLEMAS = 40            # Tamanho da população
GERACOES = 100                 # Número de gerações do algoritmo
```

### `main.py`
```python
dificuldade = 'dificil'        # Dificuldade do cenário: 'facil', 'medio', 'dificil'
service_filter = "UTEIS"       # Filtro de serviço STCP (dias úteis)
```

---

##  Resultados Esperados

O sistema apresenta:

1. **Múltiplas opções de rota** ordenadas por tempo
2. **Classificação inteligente**:
   -  **Mais Rápida**: Minimiza tempo de viagem
   -  **Mais Ecológica**: Minimiza emissões de CO2 (favorece caminhadas)
   -  **Opção Fitness**: Maximiza exercício físico (>15 min a pé)
   - ️ **Equilibrada**: Compromisso entre objetivos

3. **Informação detalhada por rota**:
   - Duração total
   - Emissões de CO2
   - Tempo a pé e calorias queimadas
   - Sequência de transbordos
   - Linhas/rotas utilizadas

---

## ️ Tecnologias Utilizadas

- **Python 3.x**
- **NetworkX**: Manipulação de grafos
- **Pandas**: Processamento de dados GTFS
- **Matplotlib**: Visualizações
- **Geopy**: Cálculo de distâncias geográficas
- **SciPy**: Estruturas de dados espaciais (KDTree)
- **NumPy**: Operações numéricas

---

##  Notas Técnicas

### Algoritmo MOEA/D
- **Decomposição**: Divide o problema multi-objetivo em 40 subproblemas escalares
- **Pesos**: Interpolação linear de 0.0 (só tempo) a 1.0 (só CO2)
- **Mutação**: Reconexão de segmentos da rota com shortest path
- **Seleção**: Tchebycheff scalarization para comparar soluções

### Penalizações
- **Tempo a pé > 20 min**: +500 minutos (hard constraint)
- **Transbordos**: +5 minutos por transbordo

### Performance
- **KDTree**: Otimiza cálculo de conexões a pé (O(n log n))
- **MultiDiGraph**: Permite consulta eficiente de múltiplas arestas
- **Cache**: Nomes de paragens pré-processados em dicionário

---

##  Licença

Projeto académico desenvolvido no âmbito da unidade curricular de **Computação Inteligente** (CIN).

---

##  Referências

- [GTFS Specification](https://gtfs.org/)
- [MOEA/D Algorithm](https://ieeexplore.ieee.org/document/4358754)
- [NetworkX Documentation](https://networkx.org/)
- [Metro do Porto - Dados Abertos](https://www.metrodoporto.pt/)
- [STCP - Dados GTFS](https://www.stcp.pt/)
- [Dados Utilizados - Portal de Dados](https://opendata.porto.digital/dataset/?q=Infraestruturas+e+Mobilidade&res_format=GTFS)
