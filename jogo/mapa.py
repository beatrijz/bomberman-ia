"""Mapa do Bomberman: grade com paredes, blocos destrutíveis, bombas, início e saída."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

PAREDE = "#"  # indestrutível, nunca pode ser atravessada
LIVRE = "."
BLOCO = "+"   # destrutível: some quando atingido por uma explosão

Posicao = Tuple[int, int]

DIRECOES = {
    "cima": (0, -1),
    "baixo": (0, 1),
    "esquerda": (-1, 0),
    "direita": (1, 0),
}


@dataclass
class Bomba:
    x: int
    y: int
    tempo: int        # tick em que explode (pode ser antecipado por reação em cadeia)
    alcance: int = 2  # quantas células o fogo avança em cada direção

    @property
    def pos(self) -> Posicao:
        return (self.x, self.y)


@dataclass
class Mapa:
    largura: int
    altura: int
    celulas: List[List[str]]
    inicio: Posicao
    objetivo: Posicao
    bombas: List[Bomba] = field(default_factory=list)

    def tipo(self, x: int, y: int) -> str:
        return self.celulas[y][x]

    def dentro(self, x: int, y: int) -> bool:
        return 0 <= x < self.largura and 0 <= y < self.altura

    def bomba_em(self, pos: Posicao) -> Optional[Bomba]:
        for bomba in self.bombas:
            if bomba.pos == pos:
                return bomba
        return None

    def com_bombas(self, bombas: List[Bomba]) -> "Mapa":
        """Cópia do mapa com outra lista de bombas (a grade é compartilhada)."""
        return Mapa(self.largura, self.altura, self.celulas, self.inicio, self.objetivo, list(bombas))


def gerar_mapa(largura: int, altura: int, densidade: float, semente: Optional[int] = None) -> Mapa:
    """Gera um mapa no padrão clássico do Bomberman.

    Borda e pilares (coordenadas pares) são paredes; as demais células recebem um bloco
    destrutível com probabilidade `densidade`. O início fica no canto superior esquerdo
    e a saída no canto inferior direito, ambos com os vizinhos livres.
    """
    if largura % 2 == 0 or altura % 2 == 0:
        raise ValueError("largura e altura devem ser ímpares")

    rng = random.Random(semente)
    inicio = (1, 1)
    objetivo = (largura - 2, altura - 2)
    # como no jogo original, o canto inicial tem um "L" livre para fugir da primeira bomba
    reservadas = {
        inicio, (2, 1), (3, 1), (1, 2), (1, 3),
        objetivo, (largura - 3, altura - 2), (largura - 2, altura - 3),
    }

    celulas = []
    for y in range(altura):
        linha = []
        for x in range(largura):
            borda = x in (0, largura - 1) or y in (0, altura - 1)
            pilar = x % 2 == 0 and y % 2 == 0
            if borda or pilar:
                linha.append(PAREDE)
            elif (x, y) in reservadas:
                linha.append(LIVRE)
            else:
                linha.append(BLOCO if rng.random() < densidade else LIVRE)
        celulas.append(linha)

    return Mapa(largura, altura, celulas, inicio, objetivo)


def bombas_aleatorias(
    mapa: Mapa,
    quantidade: int,
    rng: random.Random,
    tempo: Tuple[int, int] = (2, 10),
    alcance: Tuple[int, int] = (1, 3),
    distancia_min_inicio: int = 2,
) -> List[Bomba]:
    """Sorteia bombas em células livres, longe do início e fora da saída."""
    ocupadas = {b.pos for b in mapa.bombas}
    candidatas = [
        (x, y)
        for y in range(mapa.altura)
        for x in range(mapa.largura)
        if mapa.tipo(x, y) == LIVRE
        and (x, y) != mapa.objetivo
        and (x, y) not in ocupadas
        and abs(x - mapa.inicio[0]) + abs(y - mapa.inicio[1]) >= distancia_min_inicio
    ]
    escolhidas = rng.sample(candidatas, min(quantidade, len(candidatas)))
    return [Bomba(x, y, rng.randint(*tempo), rng.randint(*alcance)) for x, y in escolhidas]
