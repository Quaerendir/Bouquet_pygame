# Bukiet Róż 🌹

Animowana kartka z bukietem róż napisana w Pythonie z użyciem Pygame'a.

## Opis

Interaktywna animacja przedstawiająca bukiet 8 róż, które:
- Kołyszą się wiatrem (każda róża indywidualnie)
- Pulsują (efekt "oddychania")
- Reagują na ruch myszki (efekt paralaksy)
- Zrzucają pływające płatki

Efekt winietowania dodaje głębi kompozycji.

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

Projekt składa się z trzech głównych klas:

- `Rose` - pojedyncza róża z animacjami kołysania, pulsacji i efektami oświetlenia
- `FloatingPetal` - cząsteczki pływających płatków z losowym ruchem
- `Bouquet` - zarządzanie całym bukietem, sortowanie wg głębi (painter's algorithm)

## Optymalizacje

Kod został zoptymalizowany pod kątem wydajności:
- Pre-allocacja surface'i (płatków, tła, winietki) - unikanie alokacji pamięci w pętli renderingu
- Pre-render elementów statycznych (gradient tła, winietka, tekst)
- Reużywanie surface'i zamiast tworzenia nowych w każdej klatce

## Licencja

MIT
