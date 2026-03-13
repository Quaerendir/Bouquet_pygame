import pygame
import math
import sys

# Import gfxdraw jawnie, aby uniknąć błędu w pygame 2.x
try:
    import pygame.gfxdraw
except ImportError:
    print("Błąd: Nie można załadować pygame.gfxdraw. Upewnij się, że pygame jest poprawnie zainstalowane.")
    sys.exit(1)

# --- KONFIGURACJA I STAŁE ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Kolory
COLOR_BG_TOP = (35, 5, 15)       # Głębia czerwień (góra tła)
COLOR_BG_BOTTOM = (20, 0, 5)     # Prawie czarne (dół tła)
COLOR_ROSE_RED = (192, 20, 60)   # Podstawowy kolor róży
COLOR_ROSE_HIGHLIGHT = (255, 107, 138)  # Podświetlenie
COLOR_ROSE_SHADOW = (122, 0, 34)        # Cień
COLOR_STEM = (34, 139, 34)       # Zielony pęd
COLOR_LEAF = (0, 100, 0)         # Zielona liść
COLOR_RIBBON = (255, 215, 0)     # Złota wstążka

# Stałe graficzne
NUM_ROSES = 8
MAX_PETALS = 7
PETAL_LAYERS = 7
BLOOM_AMPLITUDE = 0.10  # 10% zmiana rozmiaru
SWAY_AMPLITUDE = 8.0    # px
PARALLAX_FACTOR = 0.04

# --- KLASY ---

class FloatingPetal:
    """Cząsteczka pływającego płatka"""
    def __init__(self, x, y, color):
        self.x = x + (pygame.time.get_ticks() % 100 - 50)  # lekki losowy offset
        self.y = y
        self.vx = (pygame.time.get_ticks() % 200 - 100) / 500.0  # losowa prędkość pozioma
        self.vy = 0.5 + (pygame.time.get_ticks() % 100) / 500.0  # spadanie w dół
        self.alpha = 255
        self.decay = 0.5 + (pygame.time.get_ticks() % 100) / 1000.0
        self.color = color
        self.size = 3 + (pygame.time.get_ticks() % 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= self.decay * 2
        if self.alpha < 0:
            self.alpha = 0

    def draw(self, surface):
        if self.alpha <= 0:
            return
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.gfxdraw.ellipse(s, self.size, self.size, self.size, self.size, (*self.color, int(self.alpha)))
        surface.blit(s, (self.x - self.size, self.y - self.size))


class Rose:
    """Pojedyncza róża w bukiecie"""
    def __init__(self, x, y, z, base_color):
        self.x = x
        self.y = y
        self.z = z  # 0.0 (daleko) do 1.0 (blisko)
        self.base_color = base_color
        self.phase = pygame.time.get_ticks() / 1000.0 * 0.5  # unikalny offset animacji
        self.micro_sway_phase = pygame.time.get_ticks() / 1000.0 * 1.5
        self.petal_offsets = [0.0] * PETAL_LAYERS
        for i in range(PETAL_LAYERS):
            self.petal_offsets[i] = (i * 2 * math.pi) / PETAL_LAYERS

    def get_scale(self):
        return 0.6 + self.z * 0.4  # 0.6 do 1.0

    def get_brightness(self):
        return 0.6 + self.z * 0.4  # 0.6 do 1.0

    def draw(self, surface, time):
        scale = self.get_scale()
        brightness = self.get_brightness()

        # Obliczanie pozycji z paralaksą myszki
        mx, my = pygame.mouse.get_pos()
        parallax_x = (mx - SCREEN_WIDTH / 2) * self.z * PARALLAX_FACTOR
        parallax_y = (my - SCREEN_HEIGHT / 2) * self.z * PARALLAX_FACTOR * 0.5

        cx = self.x + parallax_x
        cy = self.y + parallax_y

        # Animacja oddychania
        bloom = math.sin(time * 2 + self.phase) * BLOOM_AMPLITUDE + 1.0

        # Rysowanie pędu
        self._draw_stem(surface, cx, cy + 100 * scale, scale, brightness)

        # Rysowanie róży (od dołu do góry)
        for layer in range(PETAL_LAYERS - 1, -1, -1):
            self._draw_petal_layer(surface, cx, cy, layer, scale, bloom, brightness, time)

        # Rysowanie wstążki u podstawy
        self._draw_ribbon(surface, cx, cy + 100 * scale, scale)

    def _draw_petal_layer(self, surface, cx, cy, layer, scale, bloom, brightness, time):
        # Obliczanie rozmiaru i rotacji
        base_size = 20 + layer * 10
        size_x = base_size * scale * bloom
        size_y = base_size * scale * bloom * (0.8 + 0.2 * math.sin(time * 3 + self.phase + layer))

        # Rotacja warstwy
        rotation = self.petal_offsets[layer] + math.sin(time * 0.5 + self.phase + layer * 0.5) * 0.2

        # Kolor z uwzględnieniem jasności
        r = int(self.base_color[0] * brightness)
        g = int(self.base_color[1] * brightness)
        b = int(self.base_color[2] * brightness)

        # Rysowanie płatka jako elipsy
        s = pygame.Surface((int(size_x * 2.5), int(size_y * 2.5)), pygame.SRCALPHA)
        pygame.gfxdraw.ellipse(s, int(size_x * 1.25), int(size_y * 1.25), int(size_x), int(size_y), (r, g, b, 255))

        # Dodanie podświetlenia (lekkie odbicie światła)
        highlight = pygame.Surface((int(size_x * 2.5), int(size_y * 2.5)), pygame.SRCALPHA)
        pygame.gfxdraw.ellipse(highlight, int(size_x * 1.25), int(size_y * 1.25), int(size_x * 0.7), int(size_y * 0.7), (*COLOR_ROSE_HIGHLIGHT, int(100 * brightness)))

        # Obrót i nakładanie
        rotated = pygame.transform.rotate(s, math.degrees(rotation))
        highlight_rotated = pygame.transform.rotate(highlight, math.degrees(rotation))

        rect = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, rect.topleft)
        surface.blit(highlight_rotated, rect.topleft)

    def _draw_stem(self, surface, x, y, scale, brightness):
        # Rysowanie zakrzywionego pędu
        points = []
        for i in range(10):
            t = i / 9.0
            px = x + math.sin(t * math.pi * 0.5) * (20 * scale)
            py = y + t * (150 * scale)
            points.append((px, py))

        # Główny pęd
        if len(points) > 1:
            pygame.draw.lines(surface, (int(COLOR_STEM[0] * brightness), int(COLOR_STEM[1] * brightness), int(COLOR_STEM[2] * brightness)), False, points, int(6 * scale))

        # Rysowanie liści
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
            pygame.gfxdraw.filled_polygon(surface, leaf_points, (int(COLOR_LEAF[0] * brightness), int(COLOR_LEAF[1] * brightness), int(COLOR_LEAF[2] * brightness), 255))
            pygame.gfxdraw.aapolygon(surface, leaf_points, (int(COLOR_LEAF[0] * brightness), int(COLOR_LEAF[1] * brightness), int(COLOR_LEAF[2] * brightness), 255))

    def _draw_ribbon(self, surface, x, y, scale):
        # Rysowanie wstążki u podstawy bukietu
        ribbon_y = y + 10
        ribbon_width = 20 * scale

        # Główny węzeł
        points = [
            (x - 15 * scale, ribbon_y),
            (x - 15 * scale, ribbon_y - 10 * scale),
            (x - 5 * scale, ribbon_y - 5 * scale),
            (x + 5 * scale, ribbon_y - 10 * scale),
            (x + 15 * scale, ribbon_y),
            (x + 15 * scale, ribbon_y + 10 * scale),
            (x + 5 * scale, ribbon_y + 5 * scale),
            (x - 5 * scale, ribbon_y + 10 * scale),
        ]
        pygame.gfxdraw.filled_polygon(surface, points, COLOR_RIBBON)
        pygame.gfxdraw.aapolygon(surface, points, COLOR_RIBBON)

        # Ogonki wstążki
        pygame.draw.line(surface, COLOR_RIBBON, (x - 15 * scale, ribbon_y + 10 * scale), (x - 25 * scale, ribbon_y + 40 * scale), int(3 * scale))
        pygame.draw.line(surface, COLOR_RIBBON, (x + 15 * scale, ribbon_y + 10 * scale), (x + 25 * scale, ribbon_y + 40 * scale), int(3 * scale))


class Bouquet:
    """Zarządzanie całością bukietu"""
    def __init__(self):
        self.roses = []
        self.floating_petals = []
        self.petal_timer = 0

        # Generowanie 8 róż z losowymi parametrami
        for i in range(NUM_ROSES):
            # Losowa pozycja w obszarze bukietu
            x = SCREEN_WIDTH // 2 + (i - 3.5) * 40 + (pygame.time.get_ticks() % 20 - 10)
            y = 250 + (i % 3) * 20

            # Losowa głębokość (Z)
            z = (i % 4) / 3.0  # 0.0, 0.33, 0.66, 1.0

            # Losowa wariacja koloru
            variation = (i * 7) % 30
            base_color = (
                max(100, min(255, COLOR_ROSE_RED[0] + variation)),
                max(0, min(100, COLOR_ROSE_RED[1] - variation // 2)),
                max(30, min(150, COLOR_ROSE_RED[2] + variation // 3))
            )

            self.roses.append(Rose(x, y, z, base_color))

    def update(self, time):
        # Aktualizacja cząsteczek
        self.petal_timer += 1
        if self.petal_timer % 5 == 0:  # Co kilka klatek nowy płatek
            if self.roses:
                rose = self.roses[pygame.time.get_ticks() % len(self.roses)]
                self.floating_petals.append(FloatingPetal(
                    rose.x + (pygame.time.get_ticks() % 20 - 10),
                    rose.y - 20,
                    rose.base_color
                ))

        for petal in self.floating_petals[:]:
            petal.update()
            if petal.alpha <= 0:
                self.floating_petals.remove(petal)

    def draw(self, surface, time):
        # Obliczanie globalnego wahania bukietu
        global_sway = math.sin(time * 1.57) * SWAY_AMPLITUDE  # ok. 4s okres (2π/1.57 ≈ 4)

        # Sortowanie róż wg głębokości (od dalnych do bliskich)
        sorted_roses = sorted(self.roses, key=lambda r: r.z)

        # Rysowanie tła z gradientem
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(COLOR_BG_TOP[0] * (1 - ratio) + COLOR_BG_BOTTOM[0] * ratio)
            g = int(COLOR_BG_TOP[1] * (1 - ratio) + COLOR_BG_BOTTOM[1] * ratio)
            b = int(COLOR_BG_TOP[2] * (1 - ratio) + COLOR_BG_BOTTOM[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Rysowanie węzłów bukietu (zakrywa dolne części pędów)
        for rose in sorted_roses:
            scale = rose.get_scale()
            cx = rose.x + global_sway + (pygame.mouse.get_pos()[0] - SCREEN_WIDTH / 2) * rose.z * PARALLAX_FACTOR
            cy = rose.y + (pygame.mouse.get_pos()[1] - SCREEN_HEIGHT / 2) * rose.z * PARALLAX_FACTOR * 0.5
            ribbon_y = cy + 100 * scale + 10
            pygame.draw.circle(surface, COLOR_RIBBON, (int(cx), int(ribbon_y)), int(15 * scale))

        # Rysowanie róż
        for rose in sorted_roses:
            rose.draw(surface, time)

        # Rysowanie cząsteczek
        for petal in self.floating_petals:
            petal.draw(surface)

        # Efekt winietowania
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(vignette, (0, 0, 0, 150), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 0)
        surface.blit(vignette, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bukiet Róż")
    clock = pygame.time.Clock()

    bouquet = Bouquet()

    # Sprawdzenie systemowego fontu
    try:
        font = pygame.font.SysFont("serif", 32)
    except:
        font = pygame.font.Font(None, 32)

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

        # Aktualizacja
        bouquet.update(current_time)

        # Rysowanie
        screen.fill((0, 0, 0))
        bouquet.draw(screen, current_time)

        # Tytuł
        title_text = font.render("Wszystkiego najlepszego!", True, (255, 255, 255))
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

# --- INSTRUKCJE DO KOMPILACJI PYINSTALLER (macOS) ---
# pip install pygame pyinstaller
# 
# Kompilacja dla Intel Mac (Big Sur i nowsze):
# pyinstaller --onefile --windowed --name "Bouquet" --arch x86_64 main.py
# 
# Kompilacja dla Apple Silicon (M1/M2/M3):
# pyinstaller --onefile --windowed --name "Bouquet" --arch arm64 main.py
# 
# Jeśli wystąpią problemy z gfxdraw, dodaj: --hidden-import pygame.gfxdraw
# Wynikowy plik .app znajdziesz w katalogu dist/Bouquet.app
