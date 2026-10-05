"""Gráficos do relatório (PNG) a partir dos resumos do benchmark."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# paleta categórica validada para daltonismo (ordem fixa: azul, laranja, verde-água)
COR = {
    "A*": "#2a78d6",
    "Gulosa": "#eb6834",
    "A* espaço-tempo": "#2a78d6",
    "Gulosa espaço-tempo": "#eb6834",
    "A* ingênuo (2D)": "#1baf7a",
}
# a Gulosa é tracejada para não sumir quando coincide com o A* (ex.: 100% de sobrevivência)
TRACO = {"Gulosa": "--", "Gulosa espaço-tempo": "--"}
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
GRADE = "#e4e3df"
FUNDO = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": FUNDO,
    "axes.facecolor": FUNDO,
    "axes.edgecolor": GRADE,
    "axes.labelcolor": TEXTO_2,
    "axes.titlecolor": TEXTO,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRADE,
    "grid.linewidth": 0.8,
    "xtick.color": TEXTO_2,
    "ytick.color": TEXTO_2,
    "font.size": 10,
    "legend.frameon": False,
})


def _linhas(ax, resumo: List[Dict], x: str, y: str, serie: str, titulo: str, rotulo_y: str, rotulo_x: str):
    series = list(dict.fromkeys(r[serie] for r in resumo))
    for nome in series:
        pontos = [r for r in resumo if r[serie] == nome]
        xs, ys = [p[x] for p in pontos], [p[y] for p in pontos]
        ax.plot(xs, ys, color=COR[nome], linewidth=2, linestyle=TRACO.get(nome, "-"), marker="o", markersize=6,
                markeredgecolor=FUNDO, markeredgewidth=1.5, label=nome)
    ax.set_title(titulo, loc="left")
    ax.set_ylabel(rotulo_y)
    ax.set_xlabel(rotulo_x)
    ax.set_axisbelow(True)


def _salvar(fig, pasta: Path, nome: str):
    fig.tight_layout()
    fig.savefig(pasta / f"{nome}.png", dpi=200)
    plt.close(fig)


def grafico_tamanho(resumo, pasta):
    for r in resumo:
        r["rotulo"] = r["tamanho"]
    fig, eixos = plt.subplots(1, 3, figsize=(12, 3.8))
    _linhas(eixos[0], resumo, "celulas", "nos_expandidos", "algoritmo", "Nós expandidos", "média por mapa", "células no mapa")
    _linhas(eixos[1], resumo, "celulas", "tempo_ms", "algoritmo", "Tempo de execução", "ms", "células no mapa")
    _linhas(eixos[2], resumo, "celulas", "pct_otimo", "algoritmo", "Caminhos ótimos", "% dos mapas", "células no mapa")
    eixos[2].set_ylim(0, 105)
    for ax in eixos:
        ax.set_xscale("log")
        celulas = sorted({r["celulas"] for r in resumo})
        ax.set_xticks(celulas)
        ax.set_xticklabels([next(r["tamanho"] for r in resumo if r["celulas"] == c) for c in celulas])
        ax.minorticks_off()
    eixos[0].legend(loc="upper left")
    _salvar(fig, pasta, "1_tamanho")


def grafico_heuristica(resumo, pasta):
    fig, eixos = plt.subplots(1, 2, figsize=(11, 3.6))
    nomes = [r["configuracao"] for r in resumo]
    cores = [COR[r["algoritmo"]] for r in resumo]
    for ax, metrica, titulo, fmt in [
        (eixos[0], "nos_expandidos", "Nós expandidos (média)", "{:.0f}"),
        (eixos[1], "custo", "Custo do caminho em ticks (média)", "{:.1f}"),
    ]:
        valores = [r[metrica] for r in resumo]
        barras = ax.barh(nomes, valores, color=cores, height=0.6, edgecolor=FUNDO, linewidth=2)
        ax.invert_yaxis()
        ax.grid(axis="x", color=GRADE)
        ax.grid(axis="y", visible=False)
        ax.set_title(titulo, loc="left")
        ax.set_axisbelow(True)
        for barra, v in zip(barras, valores):
            ax.text(barra.get_width(), barra.get_y() + barra.get_height() / 2, " " + fmt.format(v),
                    va="center", color=TEXTO, fontsize=9)
        ax.set_xlim(0, max(valores) * 1.15)
    eixos[1].set_yticklabels([])
    _salvar(fig, pasta, "2_heuristica")


def grafico_densidade(resumo, pasta):
    fig, eixos = plt.subplots(1, 3, figsize=(12, 3.8))
    _linhas(eixos[0], resumo, "densidade", "nos_expandidos", "algoritmo", "Nós expandidos", "média por mapa", "% de blocos")
    _linhas(eixos[1], resumo, "densidade", "custo", "algoritmo", "Custo do caminho", "ticks", "% de blocos")
    _linhas(eixos[2], resumo, "densidade", "pct_otimo", "algoritmo", "Caminhos ótimos", "% dos mapas", "% de blocos")
    eixos[2].set_ylim(0, 105)
    for ax in eixos:
        ax.set_xticks(sorted({r["densidade"] for r in resumo}))
    eixos[0].legend(loc="upper left")
    _salvar(fig, pasta, "3_densidade")


def grafico_fuga(resumo, pasta):
    fig, eixos = plt.subplots(1, 3, figsize=(12, 3.8))
    _linhas(eixos[0], resumo, "bombas", "pct_sobreviveu", "planejador",
            "Chega vivo à saída", "% dos mapas resolvíveis", "bombas no mapa")
    _linhas(eixos[1], resumo, "bombas", "nos_expandidos", "planejador",
            "Nós expandidos", "média por mapa", "bombas no mapa")
    _linhas(eixos[2], resumo, "bombas", "tempo_ms", "planejador",
            "Tempo de execução", "ms", "bombas no mapa")
    eixos[0].set_ylim(0, 105)
    for ax in eixos:
        ax.set_xticks(sorted({r["bombas"] for r in resumo}))
    eixos[0].legend(loc="lower left")
    _salvar(fig, pasta, "4_fuga")


def gerar(resumos: Dict[str, List[Dict]], pasta: Path):
    pasta.mkdir(parents=True, exist_ok=True)
    grafico_tamanho(resumos["1_tamanho"], pasta)
    grafico_heuristica(resumos["2_heuristica"], pasta)
    grafico_densidade(resumos["3_densidade"], pasta)
    grafico_fuga(resumos["4_fuga"], pasta)
