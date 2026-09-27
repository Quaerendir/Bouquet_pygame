# Bukiet Róż 🌹

Animowana kartka z bukietem róż napisana w Pythonie z użyciem Pygame'a.

## Opis

Interaktywna animacja przedstawiająca bukiet 10 róż w papierze, przewiązany złotą kokardą:
- Róże kołyszą się wiatrem (każda indywidualnie) i delikatnie „oddychają”
- Paralaksa zależna od głębi - bliższe elementy przesuwają się mocniej za myszką
- Opadające płatki wirują i koziołkują
- Liście, gipsówka, ciepła poświata za bukietem i winietka

## Wymagania

- Python 3.8+
- pygame lub pygame-ce

```bash
pip install pygame
```

## Uruchamianie

```bash
python main.py
```

Sterowanie:
- Ruch myszki - efekt paralaksy
- Escape lub Q - wyjście

## Budowanie aplikacji

Instrukcje kompilacji dla różnych platform (macOS, Linux, Windows) znajdują się w [BUILD.md](BUILD.md).

## Architektura

- `render_*` - jednorazowy pre-render elementów statycznych (róża, papier, kokarda, tło z poświatą i winietką, napis), rysowanych w większej skali i gładko zmniejszanych (antyaliasing)
- `Rose` - pojedyncza róża: gotowy sprite obracany i skalowany w każdej klatce (kołysanie, pulsacja, paralaksa)
- `FloatingPetal` - opadający płatek z wirowaniem i zanikaniem
- `Bouquet` - kompozycja warstw od tyłu do przodu (algorytm malarza): łodygi, tył papieru, zieleń, róże wg głębi, przód papieru, kokarda, płatki

Animacja jest liczona od czasu (`dt`), nie od liczby klatek, więc tempo nie zależy od FPS. Klatka renderuje się w ~1 ms.

## Licencja

MIT - szczegóły w pliku [LICENSE](LICENSE).
