# CWL Rangliste – BonusSite

Monatliche Bonus-Rangliste der Clan War League (CWL) für unseren Clan.

🔗 **Live:** https://agdnoob.github.io/BonusSite/

## Funktionen

- Rangliste pro Saison mit Podium für die Top 3
- Rang-Veränderung zum Vormonat (▲ / ▼ / „NEU")
- Klick auf einen Spieler → Saison-Verlauf (Punkte je Monat, Bestwert, bester Rang, Top-3- und 7/7-Zähler)
- Suche, sortierbare Spalten, Schnellfilter (Alle / 7/7 / Aktiv)
- Hell-/Dunkel-Modus, vollständig handytauglich
- Reines HTML/CSS/JS in einer einzigen Datei – keine Abhängigkeiten, kein Build

## Wertung

Grundpunkte pro Angriff: Sterne (0 / 5 / 10 / 20) + 0,1 × Zerstörung %.
Gewichtet nach Rathaus-Differenz: höheres RH ×1,25 je Stufe, niedrigeres ×0,85 je Stufe (mindestens ×0,5).
Bonus: +5 bei genau 7/7 Angriffen. Jeder Account zählt einzeln.

## Daten

Die Monatsdaten liegen als `data/JJJJ-MM.json` (z. B. `data/2026-06.json`):

```json
{ "month": "Juni 2026", "players": [ { "rank": 1, "name": "…", "points": 228, "attacks": 7, "bonus": true } ] }
```

Erzeugt werden sie lokal mit `fetch_cwl_feb2026.py` über die offizielle Clash-of-Clans-API.
Dieses Script liegt **bewusst nicht im Repo** – es enthält den API-Key (siehe `.gitignore`).

**Neue Saison hinzufügen:** Script laufen lassen → neue `data/JJJJ-MM.json` committen → den Monat in der `SEASONS`-Liste in `index.html` ergänzen.

## Lokal testen

Wegen `fetch()` muss die Seite über einen Webserver laufen (nicht per Doppelklick öffnen):

```bash
python -m http.server 5501
```

Anschließend http://localhost:5501/ im Browser öffnen.

## Hosting

GitHub Pages baut automatisch aus dem `main`-Branch (Root). Die leere Datei `.nojekyll` schaltet die Jekyll-Verarbeitung ab, sodass alle Dateien unverändert ausgeliefert werden.
