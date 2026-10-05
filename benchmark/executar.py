"""Avaliação de desempenho: roda os cenários de teste e gera CSVs, tabelas e gráficos.

Uso:  python -m benchmark.executar [--sementes 30]

Cenários
  1. Tamanho do mapa     - A* x Gulosa em mapas de 15x13 até 101x101 (sem bombas)
  2. Heurística          - Manhattan, Euclidiana e Nula (Dijkstra) em mapas 31x31
  3. Densidade de blocos - 20%, 40% e 60% de blocos em mapas 31x31
  4. Fuga das explosões  - 0 a 20 bombas em mapas 21x17, com a bomba do agente no início.
                           Compara o planejamento no espaço-tempo com o A* ingênuo (2D).
"""
from __future__ import annotations

import argparse
import csv
import random
import statistics
from pathlib import Path
from typing import Dict, List

from benchmark import graficos
from ia.busca import a_estrela, busca_gulosa
from ia.heuristicas import HEURISTICAS
from ia.problema import ProblemaBomberman
from jogo.mapa import Bomba, bombas_aleatorias, gerar_mapa
from jogo.simulacao import expandir_plano, verificar_plano

PASTA = Path(__file__).resolve().parent.parent / "resultados"
BUSCAS = {"A*": a_estrela, "Gulosa": busca_gulosa}


def medir(problema, algoritmo, heuristica, cronograma_real=None) -> Dict:
    res = BUSCAS[algoritmo](problema, HEURISTICAS[heuristica])
    sobreviveu = res.sucesso
    if res.sucesso and cronograma_real is not None:
        sobreviveu = verificar_plano(expandir_plano(res.caminho), cronograma_real)[0]
    return {
        "encontrou": res.sucesso,
        "sobreviveu": sobreviveu,
        "custo": res.custo,
        "nos_expandidos": res.nos_expandidos,
        "nos_gerados": res.nos_gerados,
        "tempo_ms": res.tempo_ms,
    }


def cenario_tamanho(sementes: int) -> List[Dict]:
    linhas = []
    for largura, altura in [(15, 13), (31, 31), (61, 61), (101, 101)]:
        for s in range(sementes):
            problema = ProblemaBomberman(gerar_mapa(largura, altura, 0.4, s))
            otimo = None
            for alg in ("A*", "Gulosa"):
                m = medir(problema, alg, "Manhattan")
                otimo = otimo if otimo is not None else m["custo"]
                linhas.append({"tamanho": f"{largura}x{altura}", "celulas": largura * altura,
                               "algoritmo": alg, "semente": s, "otimo": m["custo"] == otimo, **m})
    return linhas


def cenario_heuristica(sementes: int) -> List[Dict]:
    linhas = []
    for s in range(sementes):
        problema = ProblemaBomberman(gerar_mapa(31, 31, 0.4, s))
        otimo = None
        for alg, heur in [("A*", "Manhattan"), ("A*", "Euclidiana"), ("A*", "Nula"),
                          ("Gulosa", "Manhattan"), ("Gulosa", "Euclidiana")]:
            m = medir(problema, alg, heur)
            otimo = otimo if otimo is not None else m["custo"]
            linhas.append({"configuracao": f"{alg} + {heur}", "algoritmo": alg, "heuristica": heur,
                           "semente": s, "otimo": m["custo"] == otimo, **m})
    return linhas


def cenario_densidade(sementes: int) -> List[Dict]:
    linhas = []
    for densidade in (0.2, 0.4, 0.6):
        for s in range(sementes):
            problema = ProblemaBomberman(gerar_mapa(31, 31, densidade, s))
            otimo = None
            for alg in ("A*", "Gulosa"):
                m = medir(problema, alg, "Manhattan")
                otimo = otimo if otimo is not None else m["custo"]
                linhas.append({"densidade": int(densidade * 100), "algoritmo": alg, "semente": s,
                               "otimo": m["custo"] == otimo, **m})
    return linhas


def cenario_fuga(sementes: int) -> List[Dict]:
    linhas = []
    for n_bombas in (0, 5, 10, 15, 20):
        for s in range(sementes):
            mapa = gerar_mapa(21, 17, 0.3, s)
            mapa.bombas = [Bomba(*mapa.inicio, tempo=3, alcance=2)]
            mapa.bombas += bombas_aleatorias(mapa, n_bombas, random.Random(s))
            com_tempo = ProblemaBomberman(mapa)
            ingenuo = ProblemaBomberman(mapa, considerar_tempo=False)
            real = com_tempo.cronograma
            resolvivel = None
            for nome, problema, alg in [("A* espaço-tempo", com_tempo, "A*"),
                                        ("Gulosa espaço-tempo", com_tempo, "Gulosa"),
                                        ("A* ingênuo (2D)", ingenuo, "A*")]:
                m = medir(problema, alg, "Manhattan", cronograma_real=real)
                resolvivel = m["encontrou"] if resolvivel is None else resolvivel
                linhas.append({"bombas": n_bombas, "planejador": nome, "semente": s,
                               "resolvivel": resolvivel, **m})
    return linhas


def salvar_csv(nome: str, linhas: List[Dict]):
    with open(PASTA / f"{nome}.csv", "w", newline="") as arq:
        escritor = csv.DictWriter(arq, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def resumir(linhas: List[Dict], grupo: List[str]) -> List[Dict]:
    """Média das métricas por grupo (custo só entre as execuções que encontraram caminho)."""
    grupos: Dict[tuple, List[Dict]] = {}
    for linha in linhas:
        grupos.setdefault(tuple(linha[g] for g in grupo), []).append(linha)
    resumo = []
    for chave, itens in grupos.items():
        com_caminho = [i for i in itens if i["encontrou"]]
        resolviveis = [i for i in itens if i.get("resolvivel", True)]
        linha = dict(zip(grupo, chave))
        linha.update({
            "execucoes": len(itens),
            "tempo_ms": statistics.mean(i["tempo_ms"] for i in itens),
            "nos_expandidos": statistics.mean(i["nos_expandidos"] for i in itens),
            "custo": statistics.mean(i["custo"] for i in com_caminho) if com_caminho else None,
        })
        if "otimo" in itens[0]:
            linha["pct_otimo"] = 100 * sum(i["otimo"] for i in itens) / len(itens)
        if "resolvivel" in itens[0]:
            linha["pct_resolvivel"] = 100 * len(resolviveis) / len(itens)
            linha["pct_sobreviveu"] = 100 * sum(i["sobreviveu"] for i in resolviveis) / max(1, len(resolviveis))
        resumo.append(linha)
    return resumo


def tabela_markdown(titulo: str, resumo: List[Dict]) -> str:
    colunas = list(resumo[0])
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.2f}"
        return "-" if v is None else str(v)
    linhas = [f"### {titulo}", "", "| " + " | ".join(colunas) + " |", "|" + "---|" * len(colunas)]
    linhas += ["| " + " | ".join(fmt(r[c]) for c in colunas) + " |" for r in resumo]
    return "\n".join(linhas) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sementes", type=int, default=30, help="mapas aleatórios por configuração")
    args = parser.parse_args()
    PASTA.mkdir(exist_ok=True)

    cenarios = [
        ("1_tamanho", "Cenário 1 - Tamanho do mapa", cenario_tamanho, ["tamanho", "celulas", "algoritmo"]),
        ("2_heuristica", "Cenário 2 - Heurística (31x31, 40% blocos)", cenario_heuristica, ["configuracao", "algoritmo", "heuristica"]),
        ("3_densidade", "Cenário 3 - Densidade de blocos (31x31)", cenario_densidade, ["densidade", "algoritmo"]),
        ("4_fuga", "Cenário 4 - Fuga das explosões (21x17)", cenario_fuga, ["bombas", "planejador"]),
    ]
    resumos, markdown = {}, [f"# Resultados ({args.sementes} mapas por configuração)\n"]
    for nome, titulo, funcao, grupo in cenarios:
        print(f"Rodando {titulo}...")
        linhas = funcao(args.sementes)
        salvar_csv(nome, linhas)
        resumos[nome] = resumir(linhas, grupo)
        markdown.append(tabela_markdown(titulo, resumos[nome]))

    (PASTA / "resumo.md").write_text("\n".join(markdown))
    graficos.gerar(resumos, PASTA / "graficos")
    print("\n".join(markdown))
    print(f"CSVs, resumo.md e gráficos salvos em {PASTA}")


if __name__ == "__main__":
    main()
