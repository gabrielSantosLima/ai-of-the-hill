import os

import pygame

from .config import SceneConfig
from .world import World

_CLOCK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "clock.png",
)
_INK = (25, 25, 25)


class HUD:
    def __init__(self, scene: SceneConfig):
        self.scene = scene
        self.clock_icon = self._load_clock(46)
        self.font_big = pygame.font.Font(None, 46)
        self.font = pygame.font.Font(None, 30)
        self.face_size = 30
        self.row_h = 38
        self.base_y = 66
        self._face_cache = {}
        self._row_y = {}
        self._rank = {}
        self._flash = {}
        self._flash_dur = 0.9

    @staticmethod
    def _load_clock(size: int) -> pygame.Surface:
        icon = pygame.image.load(_CLOCK_PATH).convert_alpha()
        return pygame.transform.smoothscale(icon, (size, size))

    def _face(self, color) -> pygame.Surface:
        key = (color, self.face_size)
        face = self._face_cache.get(key)
        if face is None:
            size = self.face_size
            face = pygame.Surface((size, size), pygame.SRCALPHA)
            c = size // 2
            r = c - 2
            pygame.draw.circle(face, (255, 255, 255), (c, c), r)
            pygame.draw.circle(face, color, (c, c), r, 3)
            pygame.draw.circle(face, color, (c + r // 3, c - r // 4),
                               max(2, r // 5))
            self._face_cache[key] = face
        return face

    def draw(self, screen: pygame.Surface, world: World,
             dt: float = 0.0) -> None:
        self._draw_timer(screen, world)
        self._draw_scores(screen, world, dt)
        if world.game_over:
            self._draw_winner(screen, world)

    def _draw_timer(self, screen: pygame.Surface, world: World) -> None:
        x, y = 18, 14
        screen.blit(self.clock_icon, (x, y))
        seconds = int(world.time)
        text = self.font_big.render(f"{seconds // 60:02d}:{seconds % 60:02d}",
                                    True, _INK)
        screen.blit(text, (x + self.clock_icon.get_width() + 12,
                           y + self.clock_icon.get_height() // 2 -
                           text.get_height() // 2))

    def _draw_scores(self, screen: pygame.Surface, world: World,
                     dt: float) -> None:
        ranked = sorted(world.players, key=lambda p: p.score, reverse=True)
        ranked = ranked[:self.scene.top_scores]
        right = screen.get_width() - 22
        title = self.font.render("SCORE", True, _INK)
        screen.blit(title, (right - title.get_width(), 18))
        ease = min(1.0, max(0.0, dt) * 13.0)
        for index, player in enumerate(ranked):
            key = id(player)
            target = self.base_y + index * self.row_h
            current = self._row_y.get(key, target)
            current += (target - current) * ease
            self._row_y[key] = current

            previous = self._rank.get(key)
            if previous is not None and index < previous:
                self._flash[key] = self._flash_dur
            self._rank[key] = index
            flash = self._flash.get(key, 0.0)
            if flash > 0:
                self._flash[key] = max(0.0, flash - max(0.0, dt))

            score = self.font.render(str(player.score), True, _INK)
            face = self._face(player.color)
            left = right - score.get_width() - face.get_width() - 16
            y = int(current)

            if flash > 0:
                self._draw_flash(screen, left, y, right, player.color,
                                 flash / self._flash_dur)
            screen.blit(face, (left, y))
            if player.alive:
                screen.blit(score, (right - score.get_width(), y + 2))
            else:
                ghost = score.copy()
                ghost.set_alpha(90)
                screen.blit(ghost, (right - score.get_width(), y + 2))
                pygame.draw.line(screen, _INK, (left, y + face.get_height()),
                                 (right, y + face.get_height()), 2)

    @staticmethod
    def _draw_flash(screen, left, y, right, color, ratio) -> None:
        height = 34
        panel = pygame.Surface((right - left + 12, height), pygame.SRCALPHA)
        panel.fill((*color, int(70 * ratio)))
        screen.blit(panel, (left - 6, y - 3))

    def _draw_winner(self, screen: pygame.Surface, world: World) -> None:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 190))
        screen.blit(overlay, (0, 0))
        if world.winner is None:
            message = "NO WINNER"
            color = _INK
        else:
            message = f"WINNER: {world.winner.name.upper()}"
            color = world.winner.color
        text = self.font_big.render(message, True, color)
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2,
                           screen.get_height() // 2 - text.get_height() // 2))
