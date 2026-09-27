"""Bukiet Róż - animowana kartka z bukietem róż."""

import math
import random
import sys

import pygame
import pygame.gfxdraw

# --- KONFIGURACJA I STAŁE ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Kolory
COLOR_BG_TOP = (48, 8, 24)
COLOR_BG_BOTTOM = (14, 0, 6)
COLOR_GLOW = (70, 14, 28)
COLOR_ROSE_RED = (192, 20, 60)
COLOR_ROSE_HIGHLIGHT = (255, 125, 150)
COLOR_ROSE_SHADOW = (80, 0, 22)
COLOR_STEM = (46, 110, 40)
COLOR_STEM_LIGHT = (90, 160, 70)
COLOR_LEAF = (30, 95, 35)
COLOR_LEAF_VEIN = (80, 150, 70)
COLOR_GYPSOPHILA = (250, 240, 228)
COLOR_WRAP_BACK = (140, 88, 100)
COLOR_WRAP_FRONT = (238, 206, 210)
COLOR_RIBBON = (255, 205, 60)
COLOR_RIBBON_SHADOW = (185, 130, 20)
COLOR_TITLE = (255, 236, 220)

# Kompozycja bukietu
BOUQUET_X = SCREEN_WIDTH // 2
BOUQUET_Y = 290          # środek „kopuły” kwiatów
TIE_Y = 500              # miejsce związania wstążką
STEM_END_Y = 650
# (dx, dy, z) względem środka bukietu; z: 0.0 (daleko) do 1.0 (blisko)
ROSE_LAYOUT = [
    (-120, -40, 0.1), (0, -60, 0.2), (120, -40, 0.1),
    (-170, 15, 0.4), (-60, 0, 0.5), (60, 0, 0.5), (170, 15, 0.4),
    (-95, 60, 0.85), (95, 60, 0.85), (0, 45, 1.0),
]

# Stałe graficzne
ROSE_BASE_RADIUS = 46
ROSE_TILT = 0.88         # spłaszczenie w pionie - róże widziane lekko z boku
BLOOM_AMPLITUDE = 0.03
SWAY_AMPLITUDE = 5.0
PARALLAX_FACTOR = 0.04
PARALLAX_SMOOTHING = 4.0
PETAL_SPAWN_INTERVAL = 0.35
MAX_FLOATING_PETALS = 60
SUPERSAMPLE = 3          # elementy statyczne rysowane w większej skali i zmniejszane (antyaliasing)


# --- FUNKCJE POMOCNICZE ---

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(lerp(a[i], b[i], t)) for i in range(3))


def scale_color(color: tuple, factor: float) -> tuple:
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def bezier(p0: tuple, p1: tuple, p2: tuple, steps: int) -> list:
    """Punkty kwadratowej krzywej Béziera."""
    points = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        points.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                       u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return points


def blit_centered(surface: pygame.Surface, image: pygame.Surface, x: float, y: float) -> None:
    surface.blit(image, image.get_rect(center=(round(x), round(y))))


def draw_rotated_ellipse(target, color, cx, cy, half_w, half_h, degrees, width=0) -> None:
    """Elipsa obrócona o zadany kąt (przeciwnie do ruchu wskazówek zegara)."""
    w, h = max(2, int(half_w * 2)), max(2, int(half_h * 2))
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, color, (0, 0, w, h), width)
    blit_centered(target, pygame.transform.rotate(surf, degrees), cx, cy)


def leaf_polygon(x: float, y: float, angle: float, length: float, width: float) -> list:
    """Kontur liścia od nasady (x, y) w kierunku angle."""
    ca, sa = math.cos(angle), math.sin(angle)
    left, right = [], []
    for i in range(11):
        s = i / 10
        along = s * length
        half = width * math.sin(math.pi * s) ** 0.8 * (1 - 0.35 * s)
        left.append((x + ca * along - sa * half, y + sa * along + ca * half))
        right.append((x + ca * along + sa * half, y + sa * along - ca * half))
    return left + right[::-1]


def finish_layer(big: pygame.Surface, scale: int) -> tuple:
    """Zmniejsza warstwę pełnoekranową i przycina ją do zawartości: (obraz, pozycja)."""
    small = pygame.transform.smoothscale(big, (big.get_width() // scale, big.get_height() // scale))
    rect = small.get_bounding_rect()
    return small.subsurface(rect).copy(), rect.topleft


# --- PRE-RENDER ELEMENTÓW STATYCZNYCH ---

def render_rose_sprite(radius: float, color: tuple, rng: random.Random) -> pygame.Surface:
    """Róża widziana z góry: spiralne warstwy płatków od zewnątrz do pąka w środku."""
    ss = SUPERSAMPLE
    r = radius * ss
    size = int(r * 2.3)
    c = size / 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    shadow = lerp_color(color, COLOR_ROSE_SHADOW, 0.6)
    light = lerp_color(color, COLOR_ROSE_HIGHLIGHT, 0.6)
    edge = scale_color(COLOR_ROSE_SHADOW, 0.7)

    # (liczba płatków, odległość od środka, pół-szerokość, pół-wysokość) - ułamki promienia
    layers = [(6, 0.56, 0.52, 0.42), (5, 0.42, 0.46, 0.38), (5, 0.29, 0.38, 0.32),
              (4, 0.17, 0.30, 0.26), (3, 0.07, 0.22, 0.20)]

    pygame.draw.circle(surf, shadow, (c, c), r * 0.55)
    offset = rng.uniform(0, 2 * math.pi)
    for k, (count, dist, half_w, half_h) in enumerate(layers):
        t = k / (len(layers) - 1)
        base = lerp_color(color, shadow, t * 0.7)       # im głębiej, tym ciemniej
        rim = lerp_color(light, color, t * 0.6)         # jasny brzeg płatka
        offset += math.pi / count + rng.uniform(-0.2, 0.2)
        for i in range(count):
            angle = offset + i * 2 * math.pi / count + rng.uniform(-0.15, 0.15)
            pw = half_w * r * rng.uniform(0.9, 1.1)
            ph = half_h * r * rng.uniform(0.9, 1.1)
            w, h = int(pw * 2), int(ph * 2)
            # Płatek: jasny sierp na zewnętrznej krawędzi (góra), ciemniejsze wnętrze
            petal = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(petal, rim, (0, 0, w, h))
            inset = h * 0.14
            pygame.draw.ellipse(petal, base, (w * 0.05, inset, w * 0.9, h - inset))
            pygame.draw.ellipse(petal, edge, (0, 0, w, h), ss)
            # Obrót tak, by górna krawędź płatka była skierowana od środka róży
            rotated = pygame.transform.rotate(petal, -math.degrees(angle) - 90)
            blit_centered(surf, rotated, c + math.cos(angle) * dist * r, c + math.sin(angle) * dist * r)

    # Spirala zwiniętego pąka
    spiral = []
    for i in range(60):
        th = i / 59 * 3.5 * math.pi + offset
        sr = r * (0.015 + 0.10 * i / 59)
        spiral.append((c + math.cos(th) * sr, c + math.sin(th) * sr))
    pygame.draw.lines(surf, edge, False, spiral, max(2, int(ss * 1.2)))

    return pygame.transform.smoothscale(surf, (size // ss, int(size * ROSE_TILT) // ss))


def render_wrap() -> tuple:
    """Papier bukietu: tylna część (za różami) i dwie przednie klapy."""
    ss = 2
    tx, ty = BOUQUET_X * ss, TIE_Y * ss

    def wavy_edge(x0, y0, x1, y1, waves, amp):
        pts = []
        for i in range(41):
            t = i / 40
            pts.append(((lerp(x0, x1, t)) * ss,
                        (lerp(y0, y1, t) + math.sin(t * waves * math.pi) * amp) * ss))
        return pts

    # Tylna część - wachlarz za kwiatami
    back = pygame.Surface((SCREEN_WIDTH * ss, SCREEN_HEIGHT * ss), pygame.SRCALPHA)
    top = []
    for i in range(41):
        t = i / 40
        x = lerp(-265, 265, t)
        y = 175 + 40 * (1 - (2 * t - 1) ** 2) + math.sin(t * 9 * math.pi) * 6
        top.append(((BOUQUET_X + x) * ss, y * ss))
    back_poly = top + [(tx + 22 * ss, ty), (tx - 22 * ss, ty)]
    pygame.draw.polygon(back, COLOR_WRAP_BACK, back_poly)
    for x_top in (-180, -80, 30, 140, 230):
        pygame.draw.line(back, scale_color(COLOR_WRAP_BACK, 0.8),
                         ((BOUQUET_X + x_top) * ss, 215 * ss), (tx, ty), ss)
    pygame.draw.polygon(back, scale_color(COLOR_WRAP_BACK, 0.65), back_poly, ss * 2)

    # Przednie klapy - zachodzą na siebie i przykrywają łodygi
    front = pygame.Surface((SCREEN_WIDTH * ss, SCREEN_HEIGHT * ss), pygame.SRCALPHA)
    flaps = [
        (wavy_edge(BOUQUET_X - 240, 330, BOUQUET_X + 35, 395, 5, 5),
         [(tx + 18 * ss, ty + 4 * ss), (tx - 22 * ss, ty + 4 * ss)], COLOR_WRAP_FRONT),
        (wavy_edge(BOUQUET_X - 35, 392, BOUQUET_X + 240, 330, 5, 5),
         [(tx + 22 * ss, ty + 4 * ss), (tx - 18 * ss, ty + 4 * ss)],
         lerp_color(COLOR_WRAP_FRONT, COLOR_WRAP_BACK, 0.25)),
    ]
    for edge, bottom, color in flaps:
        poly = edge + bottom
        pygame.draw.polygon(front, color, poly)
        # Fałda papieru biegnąca do miejsca związania
        mid = edge[len(edge) // 3]
        pygame.draw.line(front, scale_color(color, 0.88), mid, (tx, ty), ss * 2)
        pygame.draw.polygon(front, scale_color(color, 0.7), poly, ss * 2)

    return finish_layer(back, ss), finish_layer(front, ss)


def render_bow() -> pygame.Surface:
    """Kokarda ze wstążki: dwie pętle, dwa końce z wcięciem i węzeł."""
    ss = SUPERSAMPLE
    size_w, size_h = 180 * ss, 150 * ss
    cx, cy = size_w / 2, 45 * ss
    surf = pygame.Surface((size_w, size_h), pygame.SRCALPHA)

    # Końce wstążki
    for side in (-1, 1):
        tail = [(cx + side * 4 * ss, cy), (cx + side * 16 * ss, cy + 6 * ss),
                (cx + side * 44 * ss, cy + 95 * ss), (cx + side * 33 * ss, cy + 85 * ss),
                (cx + side * 26 * ss, cy + 100 * ss)]
        pygame.draw.polygon(surf, COLOR_RIBBON_SHADOW, tail)
        pygame.draw.polygon(surf, scale_color(COLOR_RIBBON_SHADOW, 0.75), tail, ss)

    # Pętle
    for side in (-1, 1):
        lx, ly = cx + side * 38 * ss, cy - 8 * ss
        draw_rotated_ellipse(surf, COLOR_RIBBON, lx, ly, 40 * ss, 20 * ss, -side * 22)
        draw_rotated_ellipse(surf, COLOR_RIBBON_SHADOW, lx + side * 4 * ss, ly, 24 * ss, 8 * ss, -side * 22)
        draw_rotated_ellipse(surf, COLOR_RIBBON_SHADOW, lx, ly, 40 * ss, 20 * ss, -side * 22, ss)

    # Węzeł
    knot = pygame.Rect(0, 0, 24 * ss, 22 * ss)
    knot.center = (int(cx), int(cy))
    pygame.draw.ellipse(surf, COLOR_RIBBON, knot)
    pygame.draw.ellipse(surf, COLOR_RIBBON_SHADOW, knot, ss)

    return pygame.transform.smoothscale(surf, (size_w // ss, size_h // ss))


def render_background() -> pygame.Surface:
    """Gradient, ciepła poświata za bukietem i winietka - wszystko w jednym obrazie."""
    bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        color = lerp_color(COLOR_BG_TOP, COLOR_BG_BOTTOM, y / SCREEN_HEIGHT)
        pygame.draw.line(bg, color, (0, y), (SCREEN_WIDTH, y))

    # Liczone w małej rozdzielczości i gładko skalowane - gradienty radialne bez pasów
    sw, sh = 80, 70
    glow = pygame.Surface((sw, sh))
    vignette = pygame.Surface((sw, sh), pygame.SRCALPHA)
    gx, gy = BOUQUET_X / SCREEN_WIDTH, BOUQUET_Y / SCREEN_HEIGHT
    for y in range(sh):
        for x in range(sw):
            nx, ny = (x + 0.5) / sw, (y + 0.5) / sh
            g = max(0.0, 1 - math.hypot(nx - gx, (ny - gy) * 0.9) / 0.45) ** 2
            glow.set_at((x, y), scale_color(COLOR_GLOW, g))
            d = math.hypot(nx * 2 - 1, ny * 2 - 1)
            v = max(0.0, min(1.0, (d - 0.55) / 0.85))
            vignette.set_at((x, y), (0, 0, 0, int(220 * v ** 1.5)))
    size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    bg.blit(pygame.transform.smoothscale(glow, size), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    bg.blit(pygame.transform.smoothscale(vignette, size), (0, 0))
    return bg


# --- ELEMENTY ANIMOWANE ---

class FloatingPetal:
    """Opadający płatek - wiruje, kołysze się na boki i powoli znika."""

    def __init__(self, x: float, y: float, color: tuple) -> None:
        self.base_x = x
        self.x = x
        self.y = y
        w = random.randint(9, 14)
        h = int(w * random.uniform(0.6, 0.8))
        self.sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.sprite, color, (0, 0, w, h))
        pygame.draw.ellipse(self.sprite, lerp_color(color, COLOR_ROSE_HIGHLIGHT, 0.5),
                            (w * 0.2, 0, w * 0.6, h * 0.5))
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(22, 40)
        self.wobble_amp = random.uniform(10, 22)
        self.wobble_speed = random.uniform(1.2, 2.2)
        self.wobble_phase = random.uniform(0, 2 * math.pi)
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-90, 90)
        self.flip_speed = random.uniform(2, 4)
        self.age = 0.0
        self.lifetime = random.uniform(6, 10)

    @property
    def alive(self) -> bool:
        return self.age < self.lifetime and self.y < SCREEN_HEIGHT + 20

    def update(self, dt: float) -> None:
        self.age += dt
        self.base_x += self.vx * dt
        self.x = self.base_x + math.sin(self.age * self.wobble_speed + self.wobble_phase) * self.wobble_amp
        self.y += self.vy * dt
        self.angle += self.spin * dt

    def draw(self, surface: pygame.Surface) -> None:
        fade = max(0.0, min(1.0, self.age / 0.6, (self.lifetime - self.age) / 1.5))
        # Koziołkowanie - płatek widziany na przemian płasko i z boku
        w, h = self.sprite.get_size()
        flip = abs(math.cos(self.age * self.flip_speed))
        img = pygame.transform.scale(self.sprite, (max(1, int(w * flip)), h))
        img = pygame.transform.rotate(img, self.angle)
        img.set_alpha(int(255 * fade))
        blit_centered(surface, img, self.x, self.y)


class Rose:
    """Pojedyncza róża w bukiecie."""

    def __init__(self, dx: float, dy: float, z: float, color: tuple) -> None:
        self.home_x = BOUQUET_X + dx
        self.home_y = BOUQUET_Y + dy
        self.z = z
        self.color = color
        self.radius = ROSE_BASE_RADIUS * (0.8 + 0.35 * z)
        # Dalsze róże są ciemniejsze
        self.sprite = render_rose_sprite(self.radius, scale_color(color, 0.75 + 0.25 * z), random.Random())
        self.phase = random.uniform(0, 2 * math.pi)
        self.sway_phase = random.uniform(0, 2 * math.pi)
        self.sway_amplitude = SWAY_AMPLITUDE * random.uniform(0.6, 1.2)
        self.x, self.y = self.home_x, self.home_y
        self.angle = 0.0
        self.bloom = 1.0

    def update(self, time: float, parallax: tuple) -> None:
        depth = 0.3 + self.z
        sway = math.sin(time * 0.9 + self.sway_phase) * self.sway_amplitude
        self.x = self.home_x + sway + parallax[0] * depth
        self.y = self.home_y + abs(sway) * 0.15 + parallax[1] * depth
        self.angle = -sway * 0.6
        self.bloom = 1.0 + math.sin(time * 1.4 + self.phase) * BLOOM_AMPLITUDE

    def draw(self, surface: pygame.Surface) -> None:
        blit_centered(surface, pygame.transform.rotozoom(self.sprite, self.angle, self.bloom), self.x, self.y)


class Bouquet:
    """Kompozycja: papier, łodygi, zieleń, róże, kokarda i opadające płatki."""

    def __init__(self) -> None:
        self.background = render_background()
        (self.wrap_back, self.wrap_back_pos), (self.wrap_front, self.wrap_front_pos) = render_wrap()
        self.bow = render_bow()

        self.roses = []
        for dx, dy, z in ROSE_LAYOUT:
            variation = random.randint(-15, 15)
            color = (
                max(100, min(255, COLOR_ROSE_RED[0] + variation)),
                max(0, min(100, COLOR_ROSE_RED[1] - variation // 2)),
                max(30, min(150, COLOR_ROSE_RED[2] + variation // 3)),
            )
            self.roses.append(Rose(dx, dy, z, color))
        self.roses.sort(key=lambda r: r.z)  # malowanie od najdalszej (algorytm malarza)

        # Liście wystające zza róż: (kąt, odległość od środka, długość, szerokość, faza)
        self.leaves = []
        for deg in (-175, -150, -128, -105, -78, -52, -28, -5, 160, 20):
            angle = math.radians(deg + random.uniform(-6, 6))
            self.leaves.append((angle, random.uniform(95, 120), random.uniform(55, 75),
                                random.uniform(13, 18), random.uniform(0, 2 * math.pi)))

        # Gipsówka - drobne białe kwiatki w szczelinach między różami
        self.gypsophila = []
        for deg in (-160, -135, -100, -65, -35, -12, 175):
            angle = math.radians(deg + random.uniform(-8, 8))
            dist = random.uniform(125, 150)
            cx, cy = math.cos(angle) * dist, math.sin(angle) * dist * 0.8
            dots = [(cx + random.gauss(0, 9), cy + random.gauss(0, 7), random.choice((2, 2, 3)))
                    for _ in range(12)]
            self.gypsophila.append(dots)

        self.floating_petals = []
        self.petal_timer = 0.0
        self.parallax = [0.0, 0.0]
        self.time = 0.0

    def update(self, time: float, dt: float, mouse: tuple) -> None:
        self.time = time
        # Wygładzona paralaksa - bez szarpnięć przy szybkim ruchu myszki
        target_x = (mouse[0] - SCREEN_WIDTH / 2) * PARALLAX_FACTOR
        target_y = (mouse[1] - SCREEN_HEIGHT / 2) * PARALLAX_FACTOR * 0.5
        k = min(1.0, dt * PARALLAX_SMOOTHING)
        self.parallax[0] += (target_x - self.parallax[0]) * k
        self.parallax[1] += (target_y - self.parallax[1]) * k

        for rose in self.roses:
            rose.update(time, self.parallax)

        self.petal_timer += dt
        if self.petal_timer >= PETAL_SPAWN_INTERVAL:
            self.petal_timer -= PETAL_SPAWN_INTERVAL
            if len(self.floating_petals) < MAX_FLOATING_PETALS:
                rose = random.choice(self.roses)
                self.floating_petals.append(FloatingPetal(
                    rose.x + random.uniform(-0.5, 0.5) * rose.radius,
                    rose.y + random.uniform(0, 0.3) * rose.radius,
                    rose.color,
                ))

        for petal in self.floating_petals:
            petal.update(dt)
        self.floating_petals = [p for p in self.floating_petals if p.alive]

    def _offset(self, depth: float) -> tuple:
        return self.parallax[0] * depth, self.parallax[1] * depth

    def _draw_stems(self, surface: pygame.Surface) -> None:
        tie_x, tie_y = BOUQUET_X + self._offset(0.6)[0], TIE_Y + self._offset(0.6)[1]
        for rose in self.roses:
            spread = rose.home_x - BOUQUET_X
            top = (rose.x, rose.y + rose.radius * 0.3)
            knot = (tie_x + spread * 0.05, tie_y)
            ctrl = (lerp(top[0], knot[0], 0.3), lerp(top[1], knot[1], 0.6))
            end = (tie_x + spread * 0.3, STEM_END_Y + abs(spread) * 0.1)
            points = bezier(top, ctrl, knot, 12) + [end]
            pygame.draw.lines(surface, COLOR_STEM, False, points, 5)
            pygame.draw.lines(surface, COLOR_STEM_LIGHT, False, [(x - 1, y) for x, y in points], 1)
            pygame.draw.circle(surface, scale_color(COLOR_STEM, 0.7), end, 3)

    def _draw_greenery(self, surface: pygame.Surface) -> None:
        ox, oy = self._offset(0.3)
        cx, cy = BOUQUET_X + ox, BOUQUET_Y + oy
        for angle, dist, length, width, phase in self.leaves:
            a = angle + math.sin(self.time * 0.8 + phase) * 0.05
            bx, by = cx + math.cos(a) * dist, cy + math.sin(a) * dist * 0.8
            poly = leaf_polygon(bx, by, a, length, width)
            pygame.gfxdraw.filled_polygon(surface, poly, COLOR_LEAF)
            pygame.gfxdraw.aapolygon(surface, poly, scale_color(COLOR_LEAF, 0.7))
            tip = (bx + math.cos(a) * length * 0.85, by + math.sin(a) * length * 0.85)
            pygame.draw.aaline(surface, COLOR_LEAF_VEIN, (bx, by), tip)

        ox, oy = self._offset(0.2)
        for dots in self.gypsophila:
            for dx, dy, r in dots:
                x, y = int(BOUQUET_X + ox + dx), int(BOUQUET_Y + oy + dy)
                pygame.gfxdraw.filled_circle(surface, x, y, r, COLOR_GYPSOPHILA)
                pygame.gfxdraw.aacircle(surface, x, y, r, COLOR_GYPSOPHILA)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (0, 0))

        wx, wy = self._offset(0.4)
        self._draw_stems(surface)
        surface.blit(self.wrap_back, (self.wrap_back_pos[0] + wx, self.wrap_back_pos[1] + wy))
        self._draw_greenery(surface)

        for rose in self.roses:
            rose.draw(surface)

        wx, wy = self._offset(0.6)
        surface.blit(self.wrap_front, (self.wrap_front_pos[0] + wx, self.wrap_front_pos[1] + wy))
        blit_centered(surface, self.bow, BOUQUET_X + wx, TIE_Y + wy + 30)

        for petal in self.floating_petals:
            petal.draw(surface)


def render_title() -> pygame.Surface:
    """Napis z miękkim cieniem."""
    font = pygame.font.SysFont("notoserif,dejavuserif,liberationserif,serif", 38, italic=True)
    text = font.render("Wszystkiego najlepszego!", True, COLOR_TITLE)
    shadow = font.render("Wszystkiego najlepszego!", True, (0, 0, 0))
    shadow.set_alpha(140)
    title = pygame.Surface((text.get_width() + 4, text.get_height() + 4), pygame.SRCALPHA)
    title.blit(shadow, (3, 3))
    title.blit(text, (0, 0))
    return title


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bukiet Róż")
    clock = pygame.time.Clock()

    bouquet = Bouquet()
    title = render_title()
    title_pos = title.get_rect(center=(SCREEN_WIDTH // 2, 60))

    running = True
    time = 0.0
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.1)
        time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False

        # Kursor poza oknem - paralaksa wraca do środka
        if pygame.mouse.get_focused():
            mouse = pygame.mouse.get_pos()
        else:
            mouse = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        bouquet.update(time, dt, mouse)
        bouquet.draw(screen)

        title.set_alpha(int(255 * min(1.0, time / 2.0)))  # łagodne pojawienie się napisu
        screen.blit(title, title_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
