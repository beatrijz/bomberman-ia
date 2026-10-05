"""Modelagem formal do problema de busca.

Estado:   (x, y, t) - posição do agente e o tick atual.
Ações:    mover para cima/baixo/esquerda/direita ou esperar um tick.
Custo:    duração da ação em ticks. Célula livre = 1. Célula com bloco = 1 + custo_bloco
          (tempo para quebrar o bloco antes de entrar). Esperar = 1.
Restrições:
          - paredes nunca podem ser atravessadas;
          - não é possível entrar em uma célula com bomba ainda não explodida;
          - o agente não pode estar em uma célula no tick em que ela está em chamas.
Objetivo: chegar à célula de saída.

Como o custo é o tempo, g(n) = t e o A* encontra o caminho mais rápido e seguro.
Depois do horizonte (última explosão) o mapa não muda mais, então os estados
(x, y, t) com t >= horizonte são equivalentes e colapsam em (x, y, horizonte).
Isso mantém o espaço de estados finito.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Tuple

from jogo.explosoes import Cronograma, calcular_cronograma
from jogo.mapa import DIRECOES, PAREDE, Mapa, Posicao

Estado = Tuple[int, int, int]


@dataclass
class Transicao:
    acao: str
    estado: Estado
    custo: int


class ProblemaBomberman:
    def __init__(self, mapa: Mapa, custo_bloco: int = 4, considerar_tempo: bool = True, duracao_fogo: int = 2):
        """`considerar_tempo=False` cria o planejador ingênuo: ignora bombas e explosões."""
        self.mapa = mapa
        self.custo_bloco = custo_bloco
        self.considerar_tempo = considerar_tempo
        self.cronograma = calcular_cronograma(mapa, duracao_fogo) if considerar_tempo else Cronograma()

    @property
    def objetivo(self) -> Posicao:
        return self.mapa.objetivo

    def estado_inicial(self) -> Estado:
        return (*self.mapa.inicio, 0)

    def eh_objetivo(self, estado: Estado) -> bool:
        return estado[:2] == self.mapa.objetivo

    def chave(self, estado: Estado) -> Estado:
        """Identidade do estado para a lista de fechados (colapsa o tempo após o horizonte)."""
        x, y, t = estado
        return (x, y, min(t, self.cronograma.horizonte))

    def _seguro(self, pos: Posicao, de: int, ate: int) -> bool:
        return not any(self.cronograma.perigoso(pos, t) for t in range(de, ate + 1))

    def sucessores(self, estado: Estado) -> Iterator[Transicao]:
        x, y, t = estado
        cron = self.cronograma

        for acao, (dx, dy) in DIRECOES.items():
            nx, ny = x + dx, y + dy
            destino = (nx, ny)
            if not self.mapa.dentro(nx, ny) or self.mapa.tipo(nx, ny) == PAREDE:
                continue
            if cron.tem_bomba(destino, t + 1):
                continue

            duracao = 1 + self.custo_bloco if cron.tem_bloco(self.mapa, destino, t + 1) else 1
            chegada = t + duracao
            # enquanto quebra o bloco, o agente fica parado na célula atual
            if duracao > 1 and not self._seguro((x, y), t + 1, chegada - 1):
                continue
            if cron.perigoso(destino, chegada):
                continue
            yield Transicao(acao, (nx, ny, chegada), duracao)

        # esperar só faz sentido enquanto o mapa ainda vai mudar
        if t < cron.horizonte and not cron.perigoso((x, y), t + 1):
            yield Transicao("esperar", (x, y, t + 1), 1)
