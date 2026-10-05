# Resultados (30 mapas por configuração)

### Cenário 1 - Tamanho do mapa

| tamanho | celulas | algoritmo | execucoes | tempo_ms | nos_expandidos | custo | pct_otimo |
|---|---|---|---|---|---|---|---|
| 15x13 | 195 | A* | 30 | 0.56 | 67.50 | 33.87 | 100.00 |
| 15x13 | 195 | Gulosa | 30 | 0.18 | 23 | 52.40 | 0.00 |
| 31x31 | 961 | A* | 30 | 4.11 | 481.30 | 85.87 | 100.00 |
| 31x31 | 961 | Gulosa | 30 | 0.47 | 57 | 142.27 | 0.00 |
| 61x61 | 3721 | A* | 30 | 21.26 | 2344.27 | 176 | 100.00 |
| 61x61 | 3721 | Gulosa | 30 | 1.00 | 117 | 293.07 | 0.00 |
| 101x101 | 10201 | A* | 30 | 63.20 | 6855.13 | 289.87 | 100.00 |
| 101x101 | 10201 | Gulosa | 30 | 1.71 | 197 | 513.33 | 0.00 |

### Cenário 2 - Heurística (31x31, 40% blocos)

| configuracao | algoritmo | heuristica | execucoes | tempo_ms | nos_expandidos | custo | pct_otimo |
|---|---|---|---|---|---|---|---|
| A* + Manhattan | A* | Manhattan | 30 | 4.18 | 481.30 | 85.87 | 100.00 |
| A* + Euclidiana | A* | Euclidiana | 30 | 4.71 | 555.27 | 85.87 | 100.00 |
| A* + Nula | A* | Nula | 30 | 5.29 | 637.40 | 85.87 | 100.00 |
| Gulosa + Manhattan | Gulosa | Manhattan | 30 | 0.48 | 57 | 142.27 | 0.00 |
| Gulosa + Euclidiana | Gulosa | Euclidiana | 30 | 0.55 | 57 | 138 | 0.00 |

### Cenário 3 - Densidade de blocos (31x31)

| densidade | algoritmo | execucoes | tempo_ms | nos_expandidos | custo | pct_otimo |
|---|---|---|---|---|---|---|
| 20 | A* | 30 | 1.57 | 197.13 | 60.13 | 100.00 |
| 20 | Gulosa | 30 | 0.43 | 57 | 97.20 | 0.00 |
| 40 | A* | 30 | 4.14 | 481.30 | 85.87 | 100.00 |
| 40 | Gulosa | 30 | 0.47 | 57 | 142.27 | 0.00 |
| 60 | A* | 30 | 5.62 | 603.30 | 122.80 | 100.00 |
| 60 | Gulosa | 30 | 0.51 | 57 | 183.60 | 0.00 |

### Cenário 4 - Fuga das explosões (21x17)

| bombas | planejador | execucoes | tempo_ms | nos_expandidos | custo | pct_resolvivel | pct_sobreviveu |
|---|---|---|---|---|---|---|---|
| 0 | A* espaço-tempo | 30 | 1.03 | 128.27 | 41.48 | 96.67 | 100.00 |
| 0 | Gulosa espaço-tempo | 30 | 0.26 | 32.47 | 63.31 | 96.67 | 100.00 |
| 0 | A* ingênuo (2D) | 30 | 0.94 | 117.47 | 41.33 | 96.67 | 93.10 |
| 5 | A* espaço-tempo | 30 | 1.26 | 150.73 | 38.45 | 96.67 | 100.00 |
| 5 | Gulosa espaço-tempo | 30 | 0.27 | 32.90 | 61.48 | 96.67 | 100.00 |
| 5 | A* ingênuo (2D) | 30 | 0.96 | 117.47 | 41.33 | 96.67 | 72.41 |
| 10 | A* espaço-tempo | 30 | 1.01 | 120.83 | 37.04 | 90.00 | 100.00 |
| 10 | Gulosa espaço-tempo | 30 | 0.26 | 31.47 | 59.07 | 90.00 | 100.00 |
| 10 | A* ingênuo (2D) | 30 | 0.96 | 117.47 | 41.33 | 90.00 | 51.85 |
| 15 | A* espaço-tempo | 30 | 0.82 | 98.50 | 36.36 | 83.33 | 100.00 |
| 15 | Gulosa espaço-tempo | 30 | 0.25 | 30.07 | 57.68 | 83.33 | 100.00 |
| 15 | A* ingênuo (2D) | 30 | 0.96 | 117.47 | 41.33 | 83.33 | 36.00 |
| 20 | A* espaço-tempo | 30 | 0.66 | 79.77 | 35.52 | 83.33 | 100.00 |
| 20 | Gulosa espaço-tempo | 30 | 0.25 | 30.70 | 54.68 | 83.33 | 100.00 |
| 20 | A* ingênuo (2D) | 30 | 0.94 | 117.47 | 41.33 | 83.33 | 32.00 |
