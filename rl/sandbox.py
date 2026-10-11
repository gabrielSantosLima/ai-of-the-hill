import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import pygame

_INK = (235, 238, 245)
_DIM = (150, 156, 170)
_SIDEBAR_BG = (30, 32, 40)

_INPUT_COLOR = (120, 225, 150)
_HIDDEN_COLOR = (150, 190, 255)
_OUTPUT_COLOR = (255, 225, 120)


@dataclass
class SandboxState:
    generation: int = 1
    population: int = 0
    alive: int = 0
    record: int = 0
    title: str = ""
    network: Optional[List[List[float]]] = None
    best: object = None
    ranking: List[dict] = field(default_factory=list)


class NetworkView:
    def __init__(self, rect, layers: Sequence[int] = (6, 8, 8, 1),
                 seed: int = 0, draw_counts: Optional[Sequence[int]] = None):
        self.rect = pygame.Rect(rect)
        self.draw_counts = list(draw_counts) if draw_counts else None
        self.node_radius = 12
        self._rng = random.Random(seed)
        self._glow_cache = {}
        self.time = 0.0
        self._set_layers(list(layers))

    def _set_layers(self, layers: List[int]) -> None:
        self.sizes = layers
        self.palette = self._palette(len(layers))
        self._phase = [[self._rng.uniform(0, math.tau) for _ in range(n)]
                       for n in layers]
        self._freq = [[self._rng.uniform(1.2, 2.8) for _ in range(n)]
                      for n in layers]
        self.activations = [[0.0] * n for n in layers]
        self._update_radius()

    def _update_radius(self) -> None:
        counts = self.draw_counts or self.sizes
        max_nodes = max(counts) if counts else 1
        pad_y = 26
        span = self.rect.height - 2 * pad_y
        if max_nodes > 1:
            self.node_radius = int(max(2, min(12, span / (max_nodes - 1) * 0.42)))
        else:
            self.node_radius = 12

    @staticmethod
    def _palette(count: int) -> List[tuple]:
        if count <= 1:
            return [_OUTPUT_COLOR]
        palette = []
        for i in range(count):
            if i == 0:
                palette.append(_INPUT_COLOR)
            elif i == count - 1:
                palette.append(_OUTPUT_COLOR)
            else:
                palette.append(_HIDDEN_COLOR)
        return palette

    def _ensure_layers(self, activations) -> None:
        sizes = [len(row) for row in activations]
        if sizes != self.sizes:
            self._set_layers(sizes)

    def update(self, dt: float, activations=None) -> None:
        self.time += dt
        if activations is not None:
            self._ensure_layers(activations)
            self.activations = [list(row) for row in activations]
            return
        self.activations = [
            [0.5 + 0.5 * math.sin(self.time * f + p)
             for p, f in zip(phases, freqs)]
            for phases, freqs in zip(self._phase, self._freq)
        ]

    def _positions(self):
        rect = self.rect
        layers = len(self.sizes)
        pad_x, pad_y = 40, 26
        xs = [rect.left + pad_x +
              (rect.width - 2 * pad_x) * i / max(1, layers - 1)
              for i in range(layers)]
        columns = []
        for li, count in enumerate(self.sizes):
            if count == 1:
                ys = [rect.centery]
            else:
                span = rect.height - 2 * pad_y
                ys = [rect.top + pad_y + span * i / (count - 1)
                      for i in range(count)]
            columns.append([(xs[li], y) for y in ys])
        return columns

    def _glow(self, radius: int) -> pygame.Surface:
        glow = self._glow_cache.get(radius)
        if glow is None:
            size = radius * 4
            glow = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 190, 70, 90),
                               (size // 2, size // 2), radius)
            self._glow_cache[radius] = glow
        return glow

    def draw(self, surface: pygame.Surface) -> None:
        columns = self._positions()
        for li in range(len(self.sizes) - 1):
            for (x1, y1), a1 in zip(columns[li], self.activations[li]):
                for (x2, y2), a2 in zip(columns[li + 1],
                                        self.activations[li + 1]):
                    v = max(0.0, min(1.0, min(a1, a2)))
                    color = (int(80 + 175 * v), int(85 + 80 * v),
                             int(110 - 30 * v))
                    width = 1 + int(2 * v)
                    pygame.draw.line(surface, color, (int(x1), int(y1)),
                                     (int(x2), int(y2)), width)
        radius = self.node_radius
        for li in range(len(self.sizes)):
            base = self.palette[li]
            for (x, y), a in zip(columns[li], self.activations[li]):
                a = max(0.0, min(1.0, a))
                if a > 0.2:
                    glow = self._glow(int(radius * (1.4 + a)))
                    glow.set_alpha(int(180 * a))
                    surface.blit(glow, (x - glow.get_width() / 2,
                                        y - glow.get_height() / 2))
                shade = 0.45 + 0.55 * a
                color = (int(base[0] * shade), int(base[1] * shade),
                         int(base[2] * shade))
                pygame.draw.circle(surface, color, (int(x), int(y)), radius)
                pygame.draw.circle(surface, (15, 16, 20), (int(x), int(y)),
                                   radius, 2)
        self._draw_edges(surface, columns)

    def _draw_edges(self, surface, columns) -> None:
        first_x = columns[0][0][0]
        last_x = columns[-1][0][0]
        for (x, y) in columns[0]:
            self._arrow(surface, (first_x - 30, y),
                        (x - self.node_radius - 2, y), (120, 200, 255))
        out_y = columns[-1][0][1]
        self._arrow(surface, (last_x + self.node_radius + 2, out_y),
                    (last_x + 42, out_y), _OUTPUT_COLOR)

    @staticmethod
    def _arrow(surface, start, end, color) -> None:
        pygame.draw.line(surface, color, start, end, 2)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        length = 8
        for side in (2.6, -2.6):
            tip = (end[0] + length * math.cos(angle + side),
                   end[1] + length * math.sin(angle + side))
            pygame.draw.line(surface, color, end, tip, 2)


class TrainingSandbox:
    def __init__(self, games, game_size=(1280, 640), supersample: int = 2,
                 sidebar_width: int = 480, network_layers=(6, 8, 8, 1),
                 network_draw=None, title: str = ""):
        self.games = list(games)
        self.game_size = game_size
        self.ss = max(1, supersample)
        self.sidebar_width = sidebar_width
        self.title = title
        self.gw, self.gh = game_size
        self.width = self.gw + sidebar_width
        self.height = max(self.gh, 820)
        self.game_pos = (0, (self.height - self.gh) // 2)
        self.sidebar = pygame.Rect(self.gw, 0, sidebar_width, self.height)

        self.buffers = [pygame.Surface((self.gw * self.ss, self.gh * self.ss))
                        for _ in self.games]
        self.frames = [pygame.Surface((self.gw, self.gh))
                       for _ in self.games]

        self.font_big = pygame.font.Font(None, 42)
        self.font = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 26)

        net_rect = (self.sidebar.left + 24, 226, sidebar_width - 48, 300)
        self.network = NetworkView(net_rect, network_layers,
                                   draw_counts=network_draw)

    def draw(self, screen: pygame.Surface, state: SandboxState,
             dt: float = 0.0) -> None:
        self._draw_games(screen)
        screen.fill(_SIDEBAR_BG, self.sidebar)
        pygame.draw.line(screen, (60, 64, 76), (self.gw, 0),
                         (self.gw, self.height), 3)
        self._draw_ranking(screen, state)
        self._draw_header(screen, state)
        self.network.update(dt, state.network)
        self.network.draw(screen)
        if state.best is not None:
            self._draw_best_view(screen, state.best)

    def _draw_games(self, screen: pygame.Surface) -> None:
        count = len(self.games)
        if count == 0:
            return
        if count == 1:
            display = (self.gw, self.gh)
        else:
            gap = 12
            cell = (self.gw - gap * (count + 1)) / count
            scale = cell / self.gw
            display = (int(self.gw * scale), int(self.gh * scale))
        for i, game in enumerate(self.games):
            game.render(self.buffers[i], self.ss)
            pygame.transform.smoothscale(self.buffers[i], display,
                                         self.frames[i])
            if count == 1:
                pos = (0, (self.height - self.gh) // 2)
            else:
                gap = 12
                cell = (self.gw - gap * (count + 1)) / count
                x = gap + (cell + gap) * i + (cell - display[0]) / 2
                pos = (int(x), (self.height - display[1]) // 2)
            screen.blit(self.frames[i], pos)
            pygame.draw.rect(screen, (10, 10, 12),
                             pygame.Rect(pos, display), 3)

    def _draw_ranking(self, screen: pygame.Surface,
                      state: SandboxState) -> None:
        if not state.ranking:
            return
        left = 14
        top = self.game_pos[1] + 14
        row_h = 28
        width = 210
        panel = pygame.Rect(left, top, width,
                            row_h * len(state.ranking) + 12)
        background = pygame.Surface(panel.size, pygame.SRCALPHA)
        background.fill((18, 18, 24, 175))
        screen.blit(background, panel.topleft)
        pygame.draw.rect(screen, (70, 74, 88), panel, 2)
        y = panel.top + 6
        for entry in state.ranking:
            color = entry.get("color", (255, 255, 255))
            name = entry.get("name", "?")
            score = entry.get("score", 0)
            swatch = pygame.Rect(panel.left + 8, y + 3, 16, 16)
            pygame.draw.rect(screen, color, swatch)
            pygame.draw.rect(screen, (10, 10, 12), swatch, 2)
            label = self.font_small.render(str(name), True, _INK)
            screen.blit(label, (swatch.right + 8, y))
            value = self.font_small.render(str(score), True, _OUTPUT_COLOR)
            screen.blit(value, (panel.right - 10 - value.get_width(), y))
            y += row_h

    def _draw_header(self, screen: pygame.Surface,
                     state: SandboxState) -> None:
        x = self.sidebar.left + 24
        y = 18
        if state.title:
            title = self.font_small.render(state.title, True, _DIM)
            screen.blit(title, (x, y))
            y += title.get_height() + 6
        lines = [
            (self.font_big, f"Geração: {state.generation}", _INK),
            (self.font, f"Indivíduos: {state.population}", _INK),
            (self.font, f"Vivos: {state.alive}", _INK),
        ]
        for font, text, color in lines:
            surface = font.render(text, True, color)
            screen.blit(surface, (x, y))
            y += surface.get_height() + 6
        if state.best is not None:
            name = getattr(state.best, "name", "?")
            screen.blit(self.font.render(f"Melhor: {name}", True, _INK),
                        (x, y))
            y += 34
        screen.blit(self.font.render("Recorde:", True, _DIM), (x, y))
        screen.blit(self.font.render(str(state.record), True, _OUTPUT_COLOR),
                    (x + 110, y))

    def _draw_best_view(self, screen: pygame.Surface, best) -> None:
        size = 210
        panel = pygame.Rect(0, 0, size, size)
        panel.midtop = (self.sidebar.centerx, 570)
        label = self.font_small.render("BEST INDIVIDUAL", True, _DIM)
        screen.blit(label, (panel.left, panel.top - 26))

        scale = getattr(best, "scale", 2.0)
        crop = 220
        cx = int(best.x * self.ss)
        cy = int((best.y - 19 * scale) * self.ss)
        rect = pygame.Rect(cx - crop // 2, cy - crop // 2, crop, crop)
        rect.clamp_ip(self.buffers[0].get_rect())
        view = self.buffers[0].subsurface(rect).copy()
        zoom = pygame.transform.smoothscale(view, (size, size))
        screen.blit(zoom, panel.topleft)
        pygame.draw.rect(screen, (10, 10, 12), panel, 3)
        name = getattr(best, "name", "?")
        score = getattr(best, "score", 0)
        text = self.font.render(f"{name}: {score}", True, _INK)
        screen.blit(text, (panel.left, panel.bottom + 6))
