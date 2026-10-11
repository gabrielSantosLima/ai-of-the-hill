import pygame


class Lava:
    def __init__(self, strip_path, level, window_height,
                 height_fraction=0.5, tile_scale=4):
        self.strip = pygame.image.load(strip_path).convert_alpha()
        self.frame_h = self.strip.get_height()
        self.frame_w = self.frame_h
        self.frame_count = max(1, self.strip.get_width() // self.frame_w)
        self.frames = [
            self.strip.subsurface((i * self.frame_w, 0,
                                   self.frame_w, self.frame_h)).copy()
            for i in range(self.frame_count)
        ]
        self.tile_scale = tile_scale
        min_y = min(p[1] for p in level.control_points)
        max_y = max(p[1] for p in level.control_points)
        hill_height = max_y - min_y
        self.start_y = float(window_height)
        self.target_y = max_y - hill_height * height_fraction
        self.surface_y = self.start_y
        self.active = False
        self.progress = 0.0
        self._frame = 0
        self._timer = 0.0
        self._cache = {}

    def activate(self) -> None:
        self.active = True

    def update(self, dt: float, rise_duration: float) -> None:
        if not self.active:
            return
        self.progress = min(1.0, self.progress + dt / rise_duration)
        self.surface_y = (self.start_y +
                          (self.target_y - self.start_y) * self.progress)
        self._timer += dt
        if self._timer >= 0.085:
            self._timer = 0.0
            self._frame = (self._frame + 1) % self.frame_count

    def _tile(self, ss: float) -> pygame.Surface:
        size = max(1, int(self.frame_h * self.tile_scale * ss))
        key = (self._frame, size)
        img = self._cache.get(key)
        if img is None:
            img = pygame.transform.scale(self.frames[self._frame],
                                         (size, size))
            if len(self._cache) > 12:
                self._cache.clear()
            self._cache[key] = img
        return img

    def draw(self, surface: pygame.Surface, ss: float = 1.0) -> None:
        if not self.active:
            return
        img = self._tile(ss)
        tile = img.get_width()
        width = surface.get_width()
        height = surface.get_height()
        top = int(self.surface_y * ss)
        y = top
        while y < height:
            x = 0
            while x < width:
                surface.blit(img, (x, y))
                x += tile
            y += tile
        pygame.draw.rect(surface, (255, 220, 90),
                         (0, top, width, max(1, int(2 * ss))))
