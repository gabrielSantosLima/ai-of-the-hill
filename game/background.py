import os

import pygame

_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "bg",
)
_LAYERS = ["sky.png", "clouds_small.png", "mountains_1.png",
           "clouds_big.png", "mountains_2.png"]


class Background:
    def __init__(self, veil_alpha: int = 30):
        self.layers = [
            pygame.image.load(os.path.join(_DIR, name)).convert_alpha()
            for name in _LAYERS
        ]
        self.veil_alpha = veil_alpha
        self._cache = {}

    def surface(self, scale: int) -> pygame.Surface:
        scale = int(scale)
        cached = self._cache.get(scale)
        if cached is not None:
            return cached
        width, height = self.layers[0].get_size()
        composed = pygame.Surface((width, height))
        composed.blit(self.layers[0], (0, 0))
        for layer in self.layers[1:]:
            composed.blit(layer, (0, 0))
        veil = pygame.Surface((width, height))
        veil.fill((255, 255, 255))
        veil.set_alpha(self.veil_alpha)
        composed.blit(veil, (0, 0))
        scaled = pygame.transform.scale(
            composed, (width * scale, height * scale))
        self._cache[scale] = scaled
        return scaled

    def draw(self, surface: pygame.Surface, ss: float = 1.0) -> None:
        surface.blit(self.surface(8 * int(ss)), (0, 0))
