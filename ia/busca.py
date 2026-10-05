"""Busca Gulosa (Greedy Best-First) e A*.

Os dois algoritmos são buscas de melhor-primeiro: expandem sempre o nó da fronteira
com menor f(n). A única diferença é a função de avaliação:

    Gulosa:  f(n) = h(n)          -> vai direto para o que parece mais perto da saída
    A*:      f(n) = g(n) + h(n)   -> também considera o custo já gasto

Com h admissível e consistente, o A* devolve o caminho de menor custo. A Gulosa
costuma expandir menos nós, mas não garante o ótimo.
"""
from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from ia.problema import Estado, ProblemaBomberman
from jogo.mapa import Posicao

Heuristica = Callable[[Posicao, Posicao], float]


@dataclass
class Resultado:
    algoritmo: str
    sucesso: bool
    caminho: List[Estado] = field(default_factory=list)
    acoes: List[str] = field(default_factory=list)
    custo: Optional[int] = None
    nos_expandidos: int = 0
    nos_gerados: int = 0
    tempo_ms: float = 0.0
    ordem_expansao: List[Posicao] = field(default_factory=list)


def a_estrela(problema: ProblemaBomberman, h: Heuristica) -> Resultado:
    return _melhor_primeiro(problema, h, lambda g, hn: g + hn, "A*", reabrir=True)


def busca_gulosa(problema: ProblemaBomberman, h: Heuristica) -> Resultado:
    return _melhor_primeiro(problema, h, lambda g, hn: hn, "Gulosa", reabrir=False)


def _melhor_primeiro(
    problema: ProblemaBomberman,
    h: Heuristica,
    f: Callable[[float, float], float],
    nome: str,
    reabrir: bool,
) -> Resultado:
    """Busca em grafo de melhor-primeiro.

    `reabrir=True` (A*): um estado já visto volta para a fronteira se for alcançado por
    um caminho mais barato. `reabrir=False` (Gulosa): cada estado entra uma vez só.
    """
    inicio_relogio = time.perf_counter()
    objetivo = problema.objetivo
    desempate = itertools.count()  # FIFO entre nós com o mesmo f e h

    s0 = problema.estado_inicial()
    k0 = problema.chave(s0)
    h0 = h(s0[:2], objetivo)
    fronteira = [(f(0, h0), h0, next(desempate), 0, s0)]
    melhor_g: Dict[Estado, float] = {k0: 0}
    pai: Dict[Estado, Tuple[Optional[Estado], Optional[str], Estado]] = {k0: (None, None, s0)}
    fechados = set()
    resultado = Resultado(nome, sucesso=False, nos_gerados=1)

    while fronteira:
        _, _, _, g, estado = heapq.heappop(fronteira)
        chave = problema.chave(estado)
        if chave in fechados or g > melhor_g[chave]:
            continue  # entrada obsoleta
        fechados.add(chave)
        resultado.nos_expandidos += 1
        resultado.ordem_expansao.append(estado[:2])

        if problema.eh_objetivo(estado):
            resultado.sucesso = True
            resultado.custo = g
            resultado.caminho, resultado.acoes = _reconstruir(pai, chave)
            break

        for transicao in problema.sucessores(estado):
            novo = transicao.estado
            k = problema.chave(novo)
            novo_g = g + transicao.custo
            if k in fechados:
                continue
            ja_visto = k in melhor_g
            if ja_visto and (not reabrir or novo_g >= melhor_g[k]):
                continue
            melhor_g[k] = novo_g
            pai[k] = (chave, transicao.acao, novo)
            hn = h(novo[:2], objetivo)
            heapq.heappush(fronteira, (f(novo_g, hn), hn, next(desempate), novo_g, novo))
            resultado.nos_gerados += 1

    resultado.tempo_ms = (time.perf_counter() - inicio_relogio) * 1000
    return resultado


def _reconstruir(pai, chave) -> Tuple[List[Estado], List[str]]:
    caminho, acoes = [], []
    while chave is not None:
        chave_pai, acao, estado = pai[chave]
        caminho.append(estado)
        if acao is not None:
            acoes.append(acao)
        chave = chave_pai
    return caminho[::-1], acoes[::-1]
