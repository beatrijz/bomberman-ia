"""Mostra, nó por nó, o que o A* e a Busca Gulosa expandem em mapas pequenos.

Uso:  python -m exemplos.passo_a_passo
"""
from ia.busca import a_estrela, busca_gulosa
from ia.heuristicas import manhattan
from ia.problema import ProblemaBomberman
from jogo.mapa import LIVRE, Bomba, Mapa


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


def rastrear(nome, busca, problema):
    """Embrulha `sucessores` para registrar cada estado expandido (sem mudar o algoritmo)."""
    original = problema.sucessores
    expandidos = []

    def sucessores_com_registro(estado):
        expandidos.append(estado)
        return original(estado)

    problema.sucessores = sucessores_com_registro
    resultado = busca(problema, manhattan)
    problema.sucessores = original

    print(f"\n=== {nome} ===")
    print(f"{'#':>3}  {'estado (x, y, t)':<17} {'g':>3} {'h':>3} {'g+h':>4}")
    for i, (x, y, t) in enumerate(expandidos, 1):
        h = manhattan((x, y), problema.objetivo)
        print(f"{i:>3}  {str((x, y, t)):<17} {t:>3} {h:>3.0f} {t + h:>4.0f}")
    print(f"     + saída {resultado.caminho[-1]} retirada da fronteira (objetivo)")
    print(f"ações: {' -> '.join(resultado.acoes)}")
    print(f"custo: {resultado.custo} ticks | nós expandidos: {resultado.nos_expandidos}")


def main():
    print("Exemplo 1: o bloco no meio do corredor custa 1 + 8 ticks.")
    linhas = [
        "#########",
        "#S..+..E#",
        "#.#.#.#.#",
        "#.......#",
        "#########",
    ]
    print("\n".join(linhas))
    for nome, busca in (("Gulosa", busca_gulosa), ("A*", a_estrela)):
        rastrear(nome, busca, ProblemaBomberman(mapa_de_texto(linhas), custo_bloco=8))

    print("\n\nExemplo 2: uma bomba (tempo 2, alcance 1) no corredor. O fogo dura os ticks 2 e 3.")
    linhas = [
        "#######",
        "#S.B.E#",
        "#######",
    ]
    print("\n".join(linhas))
    linhas = [linha.replace("B", ".") for linha in linhas]
    mapa = mapa_de_texto(linhas, bombas=[Bomba(3, 1, tempo=2, alcance=1)])
    rastrear("A* ingênuo (ignora a bomba)", a_estrela, ProblemaBomberman(mapa, considerar_tempo=False))
    rastrear("A* no espaço-tempo", a_estrela, ProblemaBomberman(mapa))


if __name__ == "__main__":
    main()
