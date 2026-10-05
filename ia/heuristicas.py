"""Heurísticas h(n): estimativa do custo (em ticks) da posição atual até a saída.

Todas são admissíveis: cada ação custa pelo menos 1 tick e move o agente no máximo
uma célula na horizontal ou na vertical, então nenhuma delas superestima o custo real.
"""
import math

from jogo.mapa import Posicao


def manhattan(a: Posicao, b: Posicao) -> float:
    """|dx| + |dy|: o número mínimo de passos em uma grade de 4 direções."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidiana(a: Posicao, b: Posicao) -> float:
    """Distância em linha reta: admissível, mas menos informada que Manhattan (h_E <= h_M)."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def nula(a: Posicao, b: Posicao) -> float:
    """h = 0: o A* vira Dijkstra (busca de custo uniforme). Serve de referência."""
    return 0


HEURISTICAS = {
    "Manhattan": manhattan,
    "Euclidiana": euclidiana,
    "Nula": nula,
}
