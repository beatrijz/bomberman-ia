"""Cronograma das explosões: quando e onde cada bomba vai explodir.

Como as bombas têm tempo fixo, o futuro do mapa é determinístico. O cronograma é
calculado uma vez, antes da busca, e responde em O(1) se uma célula está em chamas,
se ainda tem bomba ou se ainda tem bloco em um tick qualquer.
"""
from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set

from jogo.mapa import BLOCO, DIRECOES, PAREDE, Mapa, Posicao

INFINITO = float("inf")


@dataclass
class Cronograma:
    perigo: Dict[Posicao, Set[int]] = field(default_factory=dict)       # célula -> ticks com fogo
    bloco_destruido: Dict[Posicao, int] = field(default_factory=dict)   # célula -> tick em que o bloco some
    bomba_ate: Dict[Posicao, int] = field(default_factory=dict)         # célula tem bomba enquanto t < valor
    fogo_por_tick: Dict[int, Set[Posicao]] = field(default_factory=dict)
    explosao: List[int] = field(default_factory=list)                   # tick real de cada bomba
    horizonte: int = 0  # a partir deste tick nada mais muda no mapa

    def perigoso(self, pos: Posicao, t: int) -> bool:
        return t in self.perigo.get(pos, ())

    def tem_bomba(self, pos: Posicao, t: int) -> bool:
        return t < self.bomba_ate.get(pos, -1)

    def tem_bloco(self, mapa: Mapa, pos: Posicao, t: int) -> bool:
        return mapa.tipo(*pos) == BLOCO and t < self.bloco_destruido.get(pos, INFINITO)


def calcular_cronograma(mapa: Mapa, duracao_fogo: int = 2) -> Cronograma:
    """Simula todas as explosões, incluindo reações em cadeia.

    O fogo de uma bomba ocupa a célula dela e avança `alcance` células em cada direção,
    parando em paredes e no primeiro bloco ainda de pé (que é destruído). Uma bomba
    atingida pelo fogo explode no mesmo tick. O fogo dura `duracao_fogo` ticks.
    """
    bombas = mapa.bombas
    explosao = [b.tempo for b in bombas]
    indice_por_pos = {b.pos: i for i, b in enumerate(bombas)}
    processada = [False] * len(bombas)
    fila = [(t, i) for i, t in enumerate(explosao)]
    heapq.heapify(fila)

    perigo: Dict[Posicao, Set[int]] = defaultdict(set)
    fogo_por_tick: Dict[int, Set[Posicao]] = defaultdict(set)
    bloco_destruido: Dict[Posicao, int] = {}

    while fila:
        t, i = heapq.heappop(fila)
        if processada[i] or t != explosao[i]:
            continue
        processada[i] = True
        bomba = bombas[i]

        atingidas = [bomba.pos]
        for dx, dy in DIRECOES.values():
            for passo in range(1, bomba.alcance + 1):
                x, y = bomba.x + dx * passo, bomba.y + dy * passo
                if not mapa.dentro(x, y) or mapa.tipo(x, y) == PAREDE:
                    break
                atingidas.append((x, y))
                if mapa.tipo(x, y) == BLOCO and bloco_destruido.get((x, y), INFINITO) >= t:
                    bloco_destruido[(x, y)] = t
                    break
                j = indice_por_pos.get((x, y))
                if j is not None and not processada[j] and explosao[j] > t:
                    explosao[j] = t  # reação em cadeia
                    heapq.heappush(fila, (t, j))

        for pos in atingidas:
            for tick in range(t, t + duracao_fogo):
                perigo[pos].add(tick)
                fogo_por_tick[tick].add(pos)

    return Cronograma(
        perigo=dict(perigo),
        bloco_destruido=bloco_destruido,
        bomba_ate={b.pos: explosao[i] for i, b in enumerate(bombas)},
        fogo_por_tick=dict(fogo_por_tick),
        explosao=explosao,
        horizonte=max((t + duracao_fogo for t in explosao), default=0),
    )
