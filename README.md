# TheFinals Skin Checker

Scannt dein Waffeninventar in **The Finals** per Bildschirmanalyse,
erkennt Skin-Namen automatisch und exportiert deine gesamte Sammlung als Excel-Datei.

Kein Eingriff ins Spiel — nur passives Lesen des Bildschirms.

---

## Download

> **[Neueste Version herunterladen](../../releases/latest)**

1. Unter **Releases** den neuesten Eintrag öffnen
2. `TheFinalsStats.zip` herunterladen und entpacken
3. `TheFinalsStats.exe` starten — fertig

Keine Installation nötig. Kein Python. Kein Setup.

---

## Features

- Erkennt Waffenskins automatisch per OCR (Texterkennung)
- Zeigt Seltenheit farbig an: COMMON · RARE · EPIC · LEGENDARY · MYTHIC
- Transparentes Overlay direkt im Spiel sichtbar (klickdurchlässig)
- Capture-Bereich frei per Maus wählbar
- Exportiert alle gefundenen Skins als Excel-Datei (`.xlsx`)
- Lokale Datenbank mit ~80 Waffenskins (erweiterbar per Wiki-Scraper)
- Session wird automatisch gespeichert

---

## Benutzung

**1. Capture-Bereich wählen**
Klick auf **Select Region**, dann im Spiel den Bereich mit den Skin-Namen markieren.

**2. Scan starten**
Auf **Start Scan** klicken. Das Overlay zeigt erkannte Skins in Echtzeit.

**3. Exportieren**
Auf **Export to Excel** klicken — eine `.xlsx`-Datei wird gespeichert.

> Das Overlay lässt sich mit **Ctrl + Drag** verschieben.

---

## Seltenheiten

| Farbe | Seltenheit | Bedeutung |
|-------|-----------|-----------|
| Grau | COMMON | Immer verfügbar, kostenlos |
| Blau | RARE | Im Store erhältlich |
| Lila | EPIC | Limitiert oder Battle Pass |
| Gold | LEGENDARY | Nicht mehr erhältlich |
| Pink | MYTHIC | Extrem selten |

---

## Für Entwickler (aus dem Quellcode bauen)

**Voraussetzungen:**
- Python 3.11+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installiert

```bash
# 1. Abhängigkeiten installieren
pip install -r requirements.txt

# 2. .exe bauen (einmalig Tesseract vorbereiten + PyInstaller)
build.bat
```

Die fertige `.exe` liegt danach in `dist/TheFinalsStats/`.

---

## Hinweis

Dieses Tool interagiert **nicht** mit dem Spiel.
Es liest ausschließlich passiv den Bildschirminhalt — keine Eingabe-Automatisierung, kein Memory-Zugriff, kein Injection.
