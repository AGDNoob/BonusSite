# CWL Rangliste – BonusSite

Monatliche Bonus-Rangliste **und** Analyse-Seite der Clan War League (CWL) für den Clan *MagicDragons*.

🔗 **Live:** https://agdnoob.github.io/BonusSite/

## Funktionen

- **Rangliste** pro Saison mit Podium für die Top 3, Rang-Veränderung zum Vormonat (▲ / ▼ / „NEU"), Suche, sortierbaren Spalten und Schnellfiltern (Alle / 7/7 / Aktiv). Rathaus-Level direkt in der Liste.
- **Spielerprofile** (eigene Ansicht, teilbarer Link `#p/<name>`): aktueller Account-Status (Rathaus, Liga, Trophäen, Kriegssterne, Spenden, Rolle), Punkte-Verlauf, Rang-Verlauf, Saison-Tabelle sowie detaillierte CWL-Auswertung (Sterne-Verteilung, Angriffsziele nach Rathaus, Zuverlässigkeit).
- **Analyse** (`#a`): Clan-Snapshot, Rathaus-Verteilung, Teilnahme je Saison und All-Time-Ranglisten (Gesamtpunkte, meiste 7/7, meiste Top-3, bester Einzelwert, Konstanz) plus aktuelle Bestenlisten für Spenden, Kriegssterne und Trophäen.
- Hell-/Dunkel-Modus, vollständig handytauglich.
- Reines HTML/CSS/JS in einer einzigen Datei – keine Abhängigkeiten, kein Build.

## Wertung

Grundpunkte pro Angriff: Sterne (0 / 5 / 10 / 20) + 0,1 × Zerstörung %.
Gewichtet nach Rathaus-Differenz: höheres RH ×1,25 je Stufe, niedrigeres ×0,85 je Stufe (mindestens ×0,5).
Bonus: +5 bei genau 7/7 Angriffen. Jeder Account zählt einzeln.

## Datenstruktur

```
data/
  manifest.json        # Liste aller Saisons (Frontend lädt sie dynamisch)
  clan.json            # aktueller Clan-Snapshot + Mitglieder
  seasons/
    2026-01.json       # eine Datei pro CWL-Saison
    2026-06-2.json     # Suffix „-2" = zweite CWL im selben Monat
    …
```

Eine Saison-Datei (neues Format ab *Juni 2.0*):

```json
{ "month": "Juni 2.0", "key": "2026-06-2", "players": [
  { "rank": 1, "name": "…", "tag": "#…", "th": 15, "points": 232, "attacks": 7,
    "missed": 0, "bonus": true, "stars": 20, "s3": 6, "s2": 1, "s1": 0, "s0": 0,
    "destr": 96.4, "up": 3, "eq": 2, "down": 2 } ] }
```

Ältere Saisons (vor *Juni 2.0*) enthalten nur `rank/name/points/attacks/bonus`; die
Detail-Auswertungen erscheinen dort entsprechend nur, soweit Daten vorhanden sind.

## Daten erzeugen / aktualisieren

Erzeugt werden die Dateien lokal mit `fetch_data.py` über die offizielle Clash-of-Clans-API.

1. **API-Key** in `api_key.txt` ablegen (eine Zeile). Diese Datei bleibt **lokal** (siehe `.gitignore`).
   Alternativ die Umgebungsvariable `COC_API_KEY` setzen.
   Das Script selbst enthält **kein** Geheimnis und darf committet werden.
2. Script laufen lassen:

   ```bash
   python fetch_data.py                       # Saison = aktueller Monat (YYYY-MM)
   python fetch_data.py 2026-06-2 "Juni 2.0"  # expliziter Key + Anzeige-Label
   python fetch_data.py --no-cwl              # nur Clan-Snapshot + Manifest auffrischen
   ```

   Das Script schreibt `data/clan.json`, die jeweilige `data/seasons/<key>.json` und baut
   `data/manifest.json` neu auf (alle vorhandenen Saisons, chronologisch sortiert).
3. Änderungen committen. **Die `SEASONS`-Liste in `index.html` muss nicht mehr gepflegt werden** –
   das Frontend liest alle Saisons aus `manifest.json`.

## Lokal testen

Wegen `fetch()` muss die Seite über einen Webserver laufen (nicht per Doppelklick öffnen):

```bash
python -m http.server 5501
```

Anschließend http://localhost:5501/ im Browser öffnen.

## Hosting

GitHub Pages baut automatisch aus dem `main`-Branch (Root). Die leere Datei `.nojekyll` schaltet die Jekyll-Verarbeitung ab, sodass alle Dateien unverändert ausgeliefert werden.
