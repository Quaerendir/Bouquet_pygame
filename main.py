"""Bukiet Róż - animowana kartka z różami."""

import pygame
import pygame.gfxdraw
import math
import random
import sys

# --- KONFIGURACJA I STAŁE ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Kolory
COLOR_BG_TOP = (35, 5, 15)
COLOR_BG_BOTTOM = (20, 0, 5)
COLOR_ROSE_RED = (192, 20, 60)
COLOR_ROSE_HIGHLIGHT = (255, 107, 138)
COLOR_ROSE_SHADOW = (122, 0, 34)
COLOR_STEM = (34, 139, 34)
COLOR_LEAF = (0, 100, 0)
COLOR_RIBBON = (255, 215, 0)

# Stałe graficzne
NUM_ROSES = 8
PETAL_LAYERS = 7
BLOOM_AMPLITUDE = 0.10
SWAY_AMPLITUDE = 8.0
PARALLAX_FACTOR = 0.04


class FloatingPetal:
    """Cząsteczka pływającego płatka."""

    def __init__(self, x: float, y: float, color: tuple) -> None:
        self.x = x
        self.y = y
        self.color = color
        self.size = 3 + random.randint(0, 5)
        # Losowy kierunek początkowy z dominacją w dół
        angle = random.uniform(-math.pi * 0.3, math.pi * 0.3)
        speed = 0.4 + random.random() * 0.6
        self.vx = math.sin(angle) * speed * 0.5
        self.vy = math.cos(angle) * speed
        # Falowanie boczne
        self.wobble_phase = random.uniform(0, 2 * math.pi)
        self.wobble_speed = 1.5 + random.random() * 2.0
        self.alpha = 255
        self.decay = 0.4 + random.random() * 0.8

    def update(self, time: float) -> None:
        self.x += self.vx + math.sin(time * self.wobble_speed + self.wobble_phase) * 0.3
        self.y += self.vy
        self.alpha -= self.decay
        if self.alpha < 0:
            self.alpha = 0

    def draw(self, surface, surf: pygame.Surface) -> None:
        """Rysuje płatek na reużywanym surface'u."""
        if self.alpha <= 0:
            return
        w, h = self.size * 2, self.size * 2
        surf.fill((0, 0, 0, 0))
        pygame.gfxdraw.filled_circle(surf, self.size, self.size, self.size, (*self.color, int(self.alpha)))
        surface.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class Rose:
    """Pojedyncza róża w bukiecie."""

    def __init__(self, x: float, y: float, z: float, base_color: tuple) -> None:
        self.x = x
        self.y = y
        self.z = z  # 0.0 (daleko) do 1.0 (blisko)
        self.base_color = base_color
        # Unikalne fazy animacji
        self.phase = random.uniform(0, 2 * math.pi)
        self.sway_phase = random.uniform(0, 2 * math.pi)
        self.sway_amplitude = 3.0 + random.random() * 4.0
        self.petal_offsets = [(i * 2 * math.pi) / PETAL_LAYERS for i in range(PETAL_LAYERS)]
        # Pre-alokacja surface'i dla płatków
        self._petal_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        self._highlight_surf = pygame.Surface((100, 100), pygame.SRCALPHA)

    def get_scale(self) -> float:
        return 0.6 + self.z * 0.4

    def get_brightness(self) -> float:
        return 0.6 + self.z * 0.4

    def draw(self, surface, time: float) -> None:
        scale = self.get_scale()
        brightness = self.get_brightness()

        # Paralaksa myszki
        mx, my = pygame.mouse.get_pos()
        parallax_x = (mx - SCREEN_WIDTH / 2) * self.z * PARALLAX_FACTOR
        parallax_y = (my - SCREEN_HEIGHT / 2) * self.z * PARALLAX_FACTOR * 0.5

        # Indywidualne kołysanie
        sway_x = math.sin(time * 1.8 + self.sway_phase) * self.sway_amplitude

        cx = self.x + parallax_x + sway_x
        cy = self.y + parallax_y

        # Pulsacja
        bloom = math.sin(time * 2 + self.phase) * BLOOM_AMPLITUDE + 1.0

        # Pęd
        self._draw_stem(surface, cx, cy + 100 * scale, scale, brightness)

        # Płatki (od dołu do góry)
        for layer in range(PETAL_LAYERS - 1, -1, -1):
            self._draw_petal_layer(surface, cx, cy, layer, scale, bloom, brightness, time)

    def _draw_petal_layer(self, surface, cx, cy, layer, scale, bloom, brightness, time):
        base_size = 20 + layer * 10
        size_x = base_size * scale * bloom
        size_y = base_size * scale * bloom * (0.8 + 0.2 * math.sin(time * 3 + self.phase + layer))

        rotation = self.petal_offsets[layer] + math.sin(time * 0.5 + self.phase + layer * 0.5) * 0.2

        # Kolor z cieniowaniem
        r = int(self.base_color[0] * brightness)
        g = int(self.base_color[1] * brightness)
        b = int(self.base_color[2] * brightness)

        # Organiczny kształt płatka - elipsa z cieniowaniem radialnym
        surf = self._petal_surf
        w, h = int(size_x * 2.5), int(size_y * 2.5)
        if w > 100 or h > 100:
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            self._petal_surf = surf
        surf.fill((0, 0, 0, 0))

        # Cień na brzegu
        pygame.gfxdraw.ellipse(surf, w // 2, h // 2, int(size_x), int(size_y), (r, g, b, 255))
        # Jasne podświetlenie w środku
        hl = self._highlight_surf
        hl_w, hl_h = w, h
        if hl_w > 100 or hl_h > 100:
            hl = pygame.Surface((w, h), pygame.SRCALPHA)
            self._highlight_surf = hl
        hl.fill((0, 0, 0, 0))
        pygame.gfxdraw.ellipse(hl, w // 2, h // 2, int(size_x * 0.6), int(size_y * 0.6),
                               (*COLOR_ROSE_HIGHLIGHT, int(80 * brightness)))

        rotated = pygame.transform.rotate(surf, math.degrees(rotation))
        hl_rot = pygame.transform.rotate(hl, math.degrees(rotation))
        rect = rotated.get_rect(center=(int(cx), int(cy)))
        surface.blit(rotated, rect.topleft)
        surface.blit(hl_rot, rect.topleft)

    def _draw_stem(self, surface, x, y, scale, brightness):
        points = []
        for i in range(10):
            t = i / 9.0
            px = x + math.sin(t * math.pi * 0.5) * (20 * scale)
            py = y + t * (150 * scale)
            points.append((px, py))

        if len(points) > 1:
            stem_color = (int(COLOR_STEM[0] * brightness),
                          int(COLOR_STEM[1] * brightness),
                          int(COLOR_STEM[2] * brightness))
            pygame.draw.lines(surface, stem_color, False, points, int(6 * scale))

        # Liście
        leaf_color = (int(COLOR_LEAF[0] * brightness),
                      int(COLOR_LEAF[1] * brightness),
                      int(COLOR_LEAF[2] * brightness))
        for i in [2, 5, 8]:
            t = i / 9.0
            px = x + math.sin(t * math.pi * 0.5) * (20 * scale)
            py = y + t * (150 * scale)
            side = 1 if i % 2 == 0 else -1

            leaf_points = [
                (px, py),
                (px + side * 20 * scale, py - 10 * scale),
                (px + side * 30 * scale, py - 30 * scale),
                (px + side * 20 * scale, py - 40 * scale),
                (px, py - 30 * scale)
            ]
            pygame.gfxdraw.filled_polygon(surface, leaf_points, leaf_color)
            pygame.gfxdraw.aapolygon(surface, leaf_points, leaf_color)


class Bouquet:
    """Zarządzanie całością bukietu."""

    def __init__(self) -> None:
        self.roses = []
        self.floating_petals = []
        self.petal_timer = 0
        # Pre-renderowane tło i winietka
        self.bg_surface = self._create_background()
        self.vignette_surface = self._create_vignette()
        # Surface do pływających płatków
        self.petal_draw_surf = pygame.Surface((20, 20), pygame.SRCALPHA)

        # Generowanie róż
        for i in range(NUM_ROSES):
            x = SCREEN_WIDTH // 2 + (i - 3.5) * 40 + random.uniform(-5, 5)
            y = 250 + (i % 3) * 20
            z = (i % 4) / 3.0

            variation = random.randint(-15, 15)
            base_color = (
                max(100, min(255, COLOR_ROSE_RED[0] + variation)),
                max(0, min(100, COLOR_ROSE_RED[1] - variation // 2)),
                max(30, min(150, COLOR_ROSE_RED[2] + variation // 3))
            )

            self.roses.append(Rose(x, y, z, base_color))

    def _create_background(self) -> pygame.Surface:
        """Pre-render gradientu tła."""
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(COLOR_BG_TOP[0] * (1 - ratio) + COLOR_BG_BOTTOM[0] * ratio)
            g = int(COLOR_BG_TOP[1] * (1 - ratio) + COLOR_BG_BOTTOM[1] * ratio)
            b = int(COLOR_BG_TOP[2] * (1 - ratio) + COLOR_BG_BOTTOM[2] * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        return bg

    def _create_vignette(self) -> pygame.Surface:
        """Pre-render winietki."""
        vig = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(vig, (0, 0, 0, 150), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 0)
        return vig

    def update(self, time: float) -> None:
        self.petal_timer += 1
        if self.petal_timer % 5 == 0 and self.roses:
            rose = random.choice(self.roses)
            self.floating_petals.append(FloatingPetal(
                rose.x + random.uniform(-15, 15),
                rose.y - 20,
                rose.base_color
            ))

        for petal in self.floating_petals[:]:
            petal.update(time)
            if petal.alpha <= 0:
                self.floating_petals.remove(petal)

    def draw(self, surface, time: float) -> None:
        # Tło (pre-renderowane)
        surface.blit(self.bg_surface, (0, 0))

        # Sortowanie róż wg głębokości
        sorted_roses = sorted(self.roses, key=lambda r: r.z)

        # Rysowanie róż
        for rose in sorted_roses:
            rose.draw(surface, time)

        # Pływające płatki
        for petal in self.floating_petals:
            petal.draw(surface, self.petal_draw_surf)

        # Winietka (pre-renderowana)
        surface.blit(self.vignette_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bukiet Róż")
    clock = pygame.time.Clock()

    bouquet = Bouquet()

    try:
        font = pygame.font.SysFont("serif", 32)
    except pygame.error:
        font = pygame.font.Font(None, 32)

    # Pre-render tytułu
    title_text = font.render("Wszystkiego najlepszego!", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 36))

    running = True
    start_time = pygame.time.get_ticks() / 1000.0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

        current_time = pygame.time.get_ticks() / 1000.0 - start_time

        bouquet.update(current_time)
        bouquet.draw(screen, current_time)
        screen.blit(title_text, title_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
