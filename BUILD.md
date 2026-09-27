# Budowanie

Wymagane:
```bash
pip install pygame pyinstaller
```

## Kompilacja dla macOS

Intel Mac (Big Sur i nowsze):
```bash
pyinstaller --onefile --windowed --name "Bouquet" --arch x86_64 main.py
```

Apple Silicon (M1/M2/M3):
```bash
pyinstaller --onefile --windowed --name "Bouquet" --arch arm64 main.py
```

## Kompilacja dla Linux

```bash
pyinstaller --onefile --windowed --name "Bouquet" main.py
```

## Kompilacja dla Windows

```bash
pyinstaller --onefile --windowed --name "Bouquet" main.py
```

## Opcje debugowania

Jeśli wystąpią problemy z `pygame.gfxdraw`, dodaj:
```
--hidden-import pygame.gfxdraw
```

Wynikowy plik aplikacji znajdziesz w katalogu `dist/`.
