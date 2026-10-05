"""Interface Pygame: mapa, bombas, nós explorados, caminhos e métricas lado a lado.

Controles:
  clique esquerdo no mapa  -> coloca/remove bomba
  clique direito no mapa   -> muda a saída de lugar
  espaço                   -> anima / pausa
  setas esquerda/direita   -> volta/avança um tick
  1, 2, 3                  -> seleciona A*, Gulosa ou A* ingênuo
  N                        -> novo mapa
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import pygame

from ia.busca import Resultado, a_estrela, busca_gulosa
from ia.heuristicas import HEURISTICAS
from ia.problema import ProblemaBomberman
from jogo.explosoes import calcular_cronograma
from jogo.mapa import LIVRE, PAREDE, Bomba, bombas_aleatorias, gerar_mapa
from jogo.simulacao import blocos_quebrados_pelo_agente, expandir_plano, verificar_plano

TAMANHOS = [(15, 13), (21, 17), (31, 31), (51, 51)]
DENSIDADES = [0.2, 0.4, 0.6]
CUSTOS_BLOCO = [2, 4, 8]
TEMPO_BOMBA_USUARIO = 5
ALCANCE_BOMBA_USUARIO = 2
MS_POR_TICK = 280

LARGURA_PAINEL = 360
AREA_MAPA = (900, 780)

COR_FUNDO = (24, 26, 32)
COR_PAINEL = (34, 37, 45)
COR_TEXTO = (235, 235, 235)
COR_TEXTO_2 = (160, 165, 175)
COR_PISO = (72, 128, 64)
COR_PISO_2 = (66, 120, 58)
COR_PAREDE = (110, 112, 120)
COR_PAREDE_TOPO = (150, 152, 160)
COR_BLOCO = (168, 110, 60)
COR_BLOCO_LINHA = (120, 76, 40)
COR_FOGO = (255, 140, 30)
COR_FOGO_MIOLO = (255, 230, 110)
COR_SAIDA = (60, 150, 230)
COR_BOTAO = (55, 60, 72)
COR_BOTAO_HOVER = (75, 82, 98)
COR_ATIVO = (90, 150, 240)

ALGORITMOS = ["A*", "Gulosa", "A* ingênuo"]
COR_ALGORITMO = {"A*": (42, 120, 214), "Gulosa": (235, 104, 52), "A* ingênuo": (227, 73, 72)}
DESCRICAO = {
    "A*": "f = g + h, planeja no espaço-tempo",
    "Gulosa": "f = h, planeja no espaço-tempo",
    "A* ingênuo": "A* que ignora bombas (2D)",
}


@dataclass
class Botao:
    rotulo: Callable[[], str]
    acao: Callable[[], None]
    rect: pygame.Rect
    ativo: Callable[[], bool] = lambda: False


@dataclass
class Plano:
    resultado: Resultado
    posicoes: list
    sobreviveu: bool
    tick_falha: Optional[int]
    motivo: str
    quebrados: dict


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Bomberman IA - A* x Busca Gulosa")
        self.fonte = pygame.font.SysFont("arial", 15)
        self.fonte_pequena = pygame.font.SysFont("arial", 13)
        self.fonte_titulo = pygame.font.SysFont("arial", 20, bold=True)
        self.fonte_bomba = pygame.font.SysFont("arial", 14, bold=True)
        self.relogio = pygame.time.Clock()

        self.idx_tamanho = 0
        self.idx_densidade = 1
        self.idx_custo = 1
        self.idx_heuristica = 0
        self.semente = 1
        self.selecionado = "A*"
        self.bomba_do_agente = True
        self.mostrar_explorados = True
        self.mostrar_todos = True
        self.tocando = False
        self.tick = 0
        self.acumulado_ms = 0

        self.novo_mapa()

    # ------------------------------------------------------------------ estado
    @property
    def heuristica(self) -> str:
        return list(HEURISTICAS)[self.idx_heuristica]

    def novo_mapa(self):
        largura, altura = TAMANHOS[self.idx_tamanho]
        self.mapa_base = gerar_mapa(largura, altura, DENSIDADES[self.idx_densidade], self.semente)
        self.bombas_usuario: List[Bomba] = []
        self._configurar_janela()
        self.replanejar()

    def _configurar_janela(self):
        m = self.mapa_base
        self.celula = max(10, min(48, AREA_MAPA[0] // m.largura, AREA_MAPA[1] // m.altura))
        self.largura_mapa = m.largura * self.celula
        self.altura_mapa = m.altura * self.celula
        altura = max(self.altura_mapa, 780)
        self.tela = pygame.display.set_mode((self.largura_mapa + LARGURA_PAINEL, altura))
        self._criar_botoes()

    def bombas(self) -> List[Bomba]:
        bombas = list(self.bombas_usuario)
        if self.bomba_do_agente:
            bombas.append(Bomba(*self.mapa_base.inicio, tempo=3, alcance=ALCANCE_BOMBA_USUARIO))
        return bombas

    def replanejar(self):
        self.mapa = self.mapa_base.com_bombas(self.bombas())
        self.cronograma = calcular_cronograma(self.mapa)
        custo = CUSTOS_BLOCO[self.idx_custo]
        h = HEURISTICAS[self.heuristica]

        com_tempo = ProblemaBomberman(self.mapa, custo_bloco=custo)
        ingenuo = ProblemaBomberman(self.mapa, custo_bloco=custo, considerar_tempo=False)
        resultados = {
            "A*": a_estrela(com_tempo, h),
            "Gulosa": busca_gulosa(com_tempo, h),
            "A* ingênuo": a_estrela(ingenuo, h),
        }
        self.planos: Dict[str, Plano] = {}
        for nome, res in resultados.items():
            posicoes = expandir_plano(res.caminho)
            sobreviveu, tick_falha, motivo = verificar_plano(posicoes, self.cronograma) if res.sucesso else (False, None, "")
            self.planos[nome] = Plano(res, posicoes, sobreviveu, tick_falha, motivo, blocos_quebrados_pelo_agente(res.caminho))
        self.tick = 0
        self.tocando = False

    def tick_maximo(self) -> int:
        plano = self.planos[self.selecionado]
        fim = plano.tick_falha if plano.tick_falha is not None else len(plano.posicoes) - 1
        return max(fim, self.cronograma.horizonte, 0)

    # ------------------------------------------------------------------ botões
    def _criar_botoes(self):
        x0, y = self.largura_mapa + 16, 52
        largura, altura, espaco = LARGURA_PAINEL - 32, 28, 6
        meia = (largura - espaco) // 2

        def ciclo(attr, n):
            def f():
                setattr(self, attr, (getattr(self, attr) + 1) % n)
            return f

        def alternar(attr):
            def f():
                setattr(self, attr, not getattr(self, attr))
            return f

        def com(*acoes):
            def f():
                for acao in acoes:
                    acao()
            return f

        self.botoes: List[Botao] = []

        def linha(*defs):
            nonlocal y
            n = len(defs)
            w = largura if n == 1 else meia
            for i, (rotulo, acao, ativo) in enumerate(defs):
                rect = pygame.Rect(x0 + i * (w + espaco), y, w, altura)
                self.botoes.append(Botao(rotulo, acao, rect, ativo or (lambda: False)))
            y += altura + espaco

        for nome in ALGORITMOS:
            linha((lambda n=nome: n, lambda n=nome: setattr(self, "selecionado", n),
                   lambda n=nome: self.selecionado == n))
        y += 4
        linha((lambda: f"Heurística: {self.heuristica}", com(ciclo("idx_heuristica", len(HEURISTICAS)), self.replanejar), None))
        linha((lambda: "Mapa: %dx%d" % TAMANHOS[self.idx_tamanho], com(ciclo("idx_tamanho", len(TAMANHOS)), self.novo_mapa), None),
              (lambda: f"Blocos: {int(DENSIDADES[self.idx_densidade] * 100)}%", com(ciclo("idx_densidade", len(DENSIDADES)), self.novo_mapa), None))
        linha((lambda: f"Custo bloco: {CUSTOS_BLOCO[self.idx_custo]}", com(ciclo("idx_custo", len(CUSTOS_BLOCO)), self.replanejar), None),
              (lambda: "Novo mapa (N)", self._proxima_semente, None))
        linha((lambda: "+5 bombas", self._bombas_aleatorias, None),
              (lambda: "Limpar bombas", com(lambda: self.bombas_usuario.clear(), self.replanejar), None))
        linha((lambda: "Bomba do agente: " + ("sim" if self.bomba_do_agente else "não"),
               com(alternar("bomba_do_agente"), self.replanejar), lambda: self.bomba_do_agente))
        linha((lambda: "Explorados", alternar("mostrar_explorados"), lambda: self.mostrar_explorados),
              (lambda: "Todos caminhos", alternar("mostrar_todos"), lambda: self.mostrar_todos))
        y += 4
        linha((lambda: "Pausar (espaço)" if self.tocando else "Animar (espaço)", self._tocar, lambda: self.tocando),
              (lambda: "Reiniciar tempo", lambda: setattr(self, "tick", 0), None))
        self.y_metricas = y + 10

    def _proxima_semente(self):
        self.semente += 1
        self.novo_mapa()

    def _bombas_aleatorias(self):
        rng = random.Random(self.semente * 1000 + len(self.bombas_usuario))
        self.bombas_usuario += bombas_aleatorias(self.mapa, 5, rng)
        self.replanejar()

    def _tocar(self):
        if self.tick >= self.tick_maximo():
            self.tick = 0
        self.tocando = not self.tocando

    # ------------------------------------------------------------------ eventos
    def clique_no_mapa(self, pos, botao):
        x, y = pos[0] // self.celula, pos[1] // self.celula
        m = self.mapa_base
        if not m.dentro(x, y) or m.tipo(x, y) == PAREDE:
            return
        if botao == 1:
            existente = next((b for b in self.bombas_usuario if b.pos == (x, y)), None)
            if existente:
                self.bombas_usuario.remove(existente)
            elif m.tipo(x, y) == LIVRE and (x, y) not in (m.inicio, m.objetivo):
                self.bombas_usuario.append(Bomba(x, y, TEMPO_BOMBA_USUARIO, ALCANCE_BOMBA_USUARIO))
            else:
                return
        elif botao == 3 and (x, y) != m.inicio:
            m.celulas[y][x] = LIVRE
            m.objetivo = (x, y)
            self.bombas_usuario = [b for b in self.bombas_usuario if b.pos != (x, y)]
        else:
            return
        self.replanejar()

    def executar(self):
        while True:
            dt = self.relogio.tick(60)
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
                    pygame.quit()
                    return
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.pos[0] < self.largura_mapa:
                        self.clique_no_mapa(evento.pos, evento.button)
                    elif evento.button == 1:
                        for b in self.botoes:
                            if b.rect.collidepoint(evento.pos):
                                b.acao()
                                break
                if evento.type == pygame.KEYDOWN:
                    self._tecla(evento.key)

            if self.tocando:
                self.acumulado_ms += dt
                while self.acumulado_ms >= MS_POR_TICK:
                    self.acumulado_ms -= MS_POR_TICK
                    if self.tick < self.tick_maximo():
                        self.tick += 1
                    else:
                        self.tocando = False
            self.desenhar()

    def _tecla(self, tecla):
        if tecla == pygame.K_SPACE:
            self._tocar()
        elif tecla == pygame.K_RIGHT:
            self.tick = min(self.tick + 1, self.tick_maximo())
        elif tecla == pygame.K_LEFT:
            self.tick = max(self.tick - 1, 0)
        elif tecla == pygame.K_n:
            self._proxima_semente()
        elif tecla in (pygame.K_1, pygame.K_2, pygame.K_3):
            self.selecionado = ALGORITMOS[tecla - pygame.K_1]
            self.tick = min(self.tick, self.tick_maximo())

    # ------------------------------------------------------------------ desenho
    def desenhar(self):
        self.tela.fill(COR_FUNDO)
        self._desenhar_mapa()
        if self.mostrar_explorados and self.tick == 0 and not self.tocando:
            self._desenhar_explorados()
        self._desenhar_caminhos()
        self._desenhar_bombas_e_fogo()
        self._desenhar_agente()
        self._desenhar_painel()
        pygame.display.flip()

    def _rect(self, x, y, margem=0):
        c = self.celula
        return pygame.Rect(x * c + margem, y * c + margem, c - 2 * margem, c - 2 * margem)

    def _centro(self, pos):
        c = self.celula
        return (pos[0] * c + c // 2, pos[1] * c + c // 2)

    def _desenhar_mapa(self):
        m, c, t = self.mapa, self.celula, self.tick
        quebrados = self.planos[self.selecionado].quebrados
        for y in range(m.altura):
            for x in range(m.largura):
                r = self._rect(x, y)
                if m.tipo(x, y) == PAREDE:
                    pygame.draw.rect(self.tela, COR_PAREDE, r)
                    pygame.draw.rect(self.tela, COR_PAREDE_TOPO, (r.x, r.y, r.w, max(2, c // 6)))
                    pygame.draw.rect(self.tela, (80, 82, 90), r, 1)
                    continue
                pygame.draw.rect(self.tela, COR_PISO if (x + y) % 2 else COR_PISO_2, r)
                bloco_de_pe = self.cronograma.tem_bloco(m, (x, y), t) and t < quebrados.get((x, y), 10 ** 9)
                if bloco_de_pe:
                    pygame.draw.rect(self.tela, COR_BLOCO, r.inflate(-2, -2), border_radius=3)
                    for i in (1, 2):
                        yy = r.y + i * c // 3
                        pygame.draw.line(self.tela, COR_BLOCO_LINHA, (r.x + 2, yy), (r.right - 3, yy))
        # saída
        r = self._rect(*m.objetivo, margem=max(2, c // 8))
        pygame.draw.rect(self.tela, COR_SAIDA, r, border_radius=4)
        pygame.draw.rect(self.tela, (220, 240, 255), r, 2, border_radius=4)

    def _desenhar_explorados(self):
        plano = self.planos[self.selecionado]
        cor = COR_ALGORITMO[self.selecionado]
        camada = pygame.Surface((self.celula, self.celula), pygame.SRCALPHA)
        camada.fill((*cor, 90))
        for pos in set(plano.resultado.ordem_expansao):
            self.tela.blit(camada, self._rect(*pos).topleft)

    def _desenhar_caminhos(self):
        nomes = ALGORITMOS if self.mostrar_todos else [self.selecionado]
        deslocamento = {"A*": 0, "Gulosa": -3, "A* ingênuo": 3}
        for nome in sorted(nomes, key=lambda n: n == self.selecionado):
            plano = self.planos[nome]
            if not plano.resultado.sucesso:
                continue
            d = deslocamento[nome] * max(1, self.celula // 16)
            pontos = []
            for x, y, _ in plano.resultado.caminho:
                cx, cy = self._centro((x, y))
                if not pontos or pontos[-1] != (cx + d, cy + d):
                    pontos.append((cx + d, cy + d))
            if len(pontos) > 1:
                espessura = 4 if nome == self.selecionado else 2
                pygame.draw.lines(self.tela, COR_ALGORITMO[nome], False, pontos, espessura)

    def _desenhar_bombas_e_fogo(self):
        t, c = self.tick, self.celula
        for pos in self.cronograma.fogo_por_tick.get(t, ()):
            r = self._rect(*pos)
            pygame.draw.rect(self.tela, COR_FOGO, r)
            pygame.draw.rect(self.tela, COR_FOGO_MIOLO, r.inflate(-c // 2, -c // 2), border_radius=3)
        for bomba, explode in zip(self.mapa.bombas, self.cronograma.explosao):
            if t >= explode:
                continue
            cx, cy = self._centro(bomba.pos)
            raio = max(4, int(c * 0.36))
            pygame.draw.circle(self.tela, (20, 20, 24), (cx, cy + 1), raio)
            pygame.draw.line(self.tela, (200, 170, 120), (cx + raio // 2, cy - raio // 2), (cx + raio, cy - raio), 2)
            if c >= 18:
                texto = self.fonte_bomba.render(str(explode - t), True, (255, 220, 120))
                self.tela.blit(texto, texto.get_rect(center=(cx, cy + 1)))

    def _desenhar_agente(self):
        plano = self.planos[self.selecionado]
        if not plano.posicoes:
            pos = self.mapa.inicio
        else:
            pos = plano.posicoes[min(self.tick, len(plano.posicoes) - 1)]
        c = self.celula
        cx, cy = self._centro(pos)
        morto = plano.tick_falha is not None and self.tick >= plano.tick_falha
        raio = max(4, int(c * 0.32))
        pygame.draw.circle(self.tela, (250, 250, 250), (cx, cy), raio)
        pygame.draw.circle(self.tela, COR_ALGORITMO[self.selecionado], (cx, cy), raio, max(2, c // 12))
        if morto:
            d = raio
            pygame.draw.line(self.tela, (200, 0, 0), (cx - d, cy - d), (cx + d, cy + d), 3)
            pygame.draw.line(self.tela, (200, 0, 0), (cx - d, cy + d), (cx + d, cy - d), 3)
        elif c >= 18:
            pygame.draw.circle(self.tela, (20, 20, 24), (cx - raio // 3, cy - raio // 5), max(1, c // 16))
            pygame.draw.circle(self.tela, (20, 20, 24), (cx + raio // 3, cy - raio // 5), max(1, c // 16))

    def _texto(self, texto, pos, fonte=None, cor=COR_TEXTO):
        superficie = (fonte or self.fonte).render(texto, True, cor)
        self.tela.blit(superficie, pos)
        return superficie.get_height()

    def _desenhar_painel(self):
        x0 = self.largura_mapa
        pygame.draw.rect(self.tela, COR_PAINEL, (x0, 0, LARGURA_PAINEL, self.tela.get_height()))
        self._texto("Bomberman IA", (x0 + 16, 14), self.fonte_titulo)

        mouse = pygame.mouse.get_pos()
        for b in self.botoes:
            cor = COR_ATIVO if b.ativo() else (COR_BOTAO_HOVER if b.rect.collidepoint(mouse) else COR_BOTAO)
            pygame.draw.rect(self.tela, cor, b.rect, border_radius=5)
            rotulo = self.fonte.render(b.rotulo(), True, COR_TEXTO)
            self.tela.blit(rotulo, rotulo.get_rect(center=b.rect.center))

        y = self.y_metricas
        self._texto(f"Tick {self.tick} / {self.tick_maximo()}", (x0 + 16, y), self.fonte_titulo)
        y += 32
        colunas = [x0 + 16, x0 + 120, x0 + 185, x0 + 262]
        for i, cab in enumerate(["Algoritmo", "Custo", "Nós exp.", "Tempo"]):
            self._texto(cab, (colunas[i], y), self.fonte_pequena, COR_TEXTO_2)
        y += 20
        for nome in ALGORITMOS:
            plano = self.planos[nome]
            res = plano.resultado
            pygame.draw.rect(self.tela, COR_ALGORITMO[nome], (colunas[0], y + 4, 10, 10), border_radius=2)
            self._texto(nome, (colunas[0] + 16, y))
            self._texto("-" if res.custo is None else str(res.custo), (colunas[1], y))
            self._texto(str(res.nos_expandidos), (colunas[2], y))
            self._texto(f"{res.tempo_ms:.2f} ms", (colunas[3], y))
            y += 19
            if not res.sucesso:
                status, cor = "sem caminho seguro", (240, 170, 80)
            elif plano.sobreviveu:
                status, cor = "chega à saída com segurança", (130, 210, 130)
            else:
                status, cor = f"falha no tick {plano.tick_falha}: {plano.motivo}", (240, 110, 110)
            self._texto(status, (colunas[0] + 16, y), self.fonte_pequena, cor)
            y += 24

        y += 6
        self._texto(DESCRICAO[self.selecionado], (x0 + 16, y), self.fonte_pequena, COR_TEXTO_2)
        y += 26
        for linha in [
            "Clique esq.: coloca/remove bomba",
            "Clique dir.: move a saída",
            "Setas: avança/volta um tick",
            "1 / 2 / 3: escolhe o algoritmo",
        ]:
            self._texto(linha, (x0 + 16, y), self.fonte_pequena, COR_TEXTO_2)
            y += 18
