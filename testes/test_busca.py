import random

import pytest

from ia.busca import a_estrela, busca_gulosa
from ia.heuristicas import euclidiana, manhattan, nula
from ia.problema import ProblemaBomberman
from jogo.explosoes import calcular_cronograma
from jogo.mapa import LIVRE, Bomba, Mapa, bombas_aleatorias, gerar_mapa
from jogo.simulacao import expandir_plano, verificar_plano


def mapa_de_texto(linhas, bombas=()):
    """'S' = início, 'E' = saída, '#' = parede, '+' = bloco, '.' = livre."""
    celulas, inicio, objetivo = [], None, None
    for y, linha in enumerate(linhas):
        linha_celulas = []
        for x, c in enumerate(linha):
            if c == "S":
                inicio, c = (x, y), LIVRE
            elif c == "E":
                objetivo, c = (x, y), LIVRE
            linha_celulas.append(c)
        celulas.append(linha_celulas)
    return Mapa(len(linhas[0]), len(linhas), celulas, inicio, objetivo, list(bombas))


def mapas_aleatorios(com_bombas):
    for semente in range(25):
        rng = random.Random(semente)
        mapa = gerar_mapa(15, 13, densidade=0.4, semente=semente)
        if com_bombas:
            mapa.bombas = bombas_aleatorias(mapa, 8, rng)
        yield mapa


@pytest.mark.parametrize("com_bombas", [False, True])
def test_a_estrela_encontra_o_mesmo_custo_que_dijkstra(com_bombas):
    for mapa in mapas_aleatorios(com_bombas):
        problema = ProblemaBomberman(mapa)
        dijkstra = a_estrela(problema, nula)
        for h in (manhattan, euclidiana):
            resultado = a_estrela(problema, h)
            assert resultado.sucesso == dijkstra.sucesso
            assert resultado.custo == dijkstra.custo


@pytest.mark.parametrize("com_bombas", [False, True])
def test_gulosa_nunca_e_melhor_que_o_otimo(com_bombas):
    for mapa in mapas_aleatorios(com_bombas):
        problema = ProblemaBomberman(mapa)
        otimo = a_estrela(problema, manhattan)
        gulosa = busca_gulosa(problema, manhattan)
        assert gulosa.sucesso == otimo.sucesso  # ambas são completas em espaço finito
        if otimo.sucesso:
            assert gulosa.custo >= otimo.custo


def test_planos_com_tempo_sobrevivem_as_explosoes():
    for mapa in mapas_aleatorios(com_bombas=True):
        problema = ProblemaBomberman(mapa)
        for busca in (a_estrela, busca_gulosa):
            resultado = busca(problema, manhattan)
            if resultado.sucesso:
                posicoes = expandir_plano(resultado.caminho)
                assert len(posicoes) - 1 == resultado.custo
                assert verificar_plano(posicoes, problema.cronograma)[0]


def test_custo_do_bloco_e_contabilizado():
    mapa = mapa_de_texto([
        "#####",
        "#S+E#",
        "#####",
    ])
    resultado = a_estrela(ProblemaBomberman(mapa, custo_bloco=4), manhattan)
    assert resultado.custo == 1 + 4 + 1


def test_agente_espera_a_explosao_passar():
    # A bomba explode no tick 2 e queima o corredor nos ticks 2 e 3.
    mapa = mapa_de_texto([
        "#######",
        "#S...E#",
        "#######",
    ], bombas=[Bomba(3, 1, tempo=2, alcance=1)])

    ingenuo = a_estrela(ProblemaBomberman(mapa, considerar_tempo=False), manhattan)
    cronograma = calcular_cronograma(mapa)
    sobreviveu, _, _ = verificar_plano(expandir_plano(ingenuo.caminho), cronograma)
    assert not sobreviveu

    com_tempo = a_estrela(ProblemaBomberman(mapa), manhattan)
    assert com_tempo.sucesso
    assert "esperar" in com_tempo.acoes
    assert verificar_plano(expandir_plano(com_tempo.caminho), cronograma)[0]


def test_agente_foge_da_propria_bomba():
    mapa = mapa_de_texto([
        "#########",
        "#S.....E#",
        "#.#######",
        "#.#######",
        "#########",
    ], bombas=[Bomba(1, 1, tempo=5, alcance=3)])
    resultado = a_estrela(ProblemaBomberman(mapa), manhattan)
    assert resultado.sucesso
    assert verificar_plano(expandir_plano(resultado.caminho), calcular_cronograma(mapa))[0]


def test_explosao_para_na_parede_e_no_bloco():
    mapa = mapa_de_texto([
        "#######",
        "#S.+..#",
        "#.#.#.#",
        "#....E#",
        "#######",
    ], bombas=[Bomba(1, 1, tempo=1, alcance=3)])
    cron = calcular_cronograma(mapa)
    assert cron.perigoso((3, 1), 1)          # o bloco é atingido...
    assert not cron.perigoso((4, 1), 1)      # ...e segura o fogo
    assert cron.bloco_destruido[(3, 1)] == 1
    assert cron.perigoso((1, 3), 1)
    assert not cron.perigoso((1, 4), 1)      # borda é parede


def test_reacao_em_cadeia():
    mapa = mapa_de_texto([
        "#######",
        "#S...E#",
        "#######",
    ], bombas=[Bomba(2, 1, tempo=2, alcance=2), Bomba(4, 1, tempo=9, alcance=1)])
    cron = calcular_cronograma(mapa)
    assert cron.explosao == [2, 2]
