"""Execução de um plano no tempo: posição do agente a cada tick e verificação de sobrevivência."""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from jogo.explosoes import Cronograma
from jogo.mapa import Posicao

Estado = Tuple[int, int, int]


def expandir_plano(caminho: Sequence[Estado]) -> List[Posicao]:
    """Converte o caminho de estados (x, y, t) em uma posição por tick.

    Atravessar um bloco dura 1 + custo_bloco ticks: o agente fica parado na célula atual
    enquanto quebra o bloco e só depois avança.
    """
    if not caminho:
        return []
    posicoes = [caminho[0][:2]]
    for (x, y, t), (nx, ny, nt) in zip(caminho, caminho[1:]):
        posicoes.extend([(x, y)] * (nt - t - 1))
        posicoes.append((nx, ny))
    return posicoes


def blocos_quebrados_pelo_agente(caminho: Sequence[Estado]) -> Dict[Posicao, int]:
    """Células de bloco atravessadas pelo agente -> tick em que ele entra nelas."""
    quebrados = {}
    for (x, y, t), (nx, ny, nt) in zip(caminho, caminho[1:]):
        if (nx, ny) != (x, y) and nt - t > 1:
            quebrados[(nx, ny)] = nt
    return quebrados


def verificar_plano(posicoes: Sequence[Posicao], cronograma: Cronograma) -> Tuple[bool, Optional[int], str]:
    """Executa o plano contra o cronograma real. Retorna (sobreviveu, tick_da_falha, motivo)."""
    for t, pos in enumerate(posicoes):
        if cronograma.perigoso(pos, t):
            return False, t, "atingido pela explosão"
        if t > 0 and pos != posicoes[t - 1] and cronograma.tem_bomba(pos, t):
            return False, t, "bloqueado por bomba"
    return True, None, ""
