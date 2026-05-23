# Core

## Erweiterungsstrategie für Namer: Core bleibt unangetastet

Diese Datei beschreibt die Architekturidee, Vorgehensweise und Erweiterungsstrategie für einen eigenen Namer-Ausbau.
Das zentrale Prinzip lautet:

> **Namer bleibt der Core und wird möglichst nicht direkt verändert.**
> Eigene Funktionen werden außen herum gebaut, damit Updates aus dem Original-Repository weiterhin einfach möglich bleiben.

---

## 1. Ziel

Namer soll um zusätzliche Funktionen erweitert werden, ohne dass der eigentliche Namer-Core stark verändert wird.

Ziele:

- Original-Namer weiterhin schnell aktualisieren können
- eigene Features unabhängig entwickeln
- Merge-Konflikte mit Upstream vermeiden
- Docker-/Proxmox-/Homelab-tauglich bleiben
- optionale KI-Unterstützung über Ollama ermöglichen
- StashApp, StashDB und CommunityScraper als Metadatenquellen nutzen
- unsichere Treffer kontrolliert prüfen statt blind automatisch umzubenennen

Nicht-Ziele:

- Namer komplett neu schreiben
- Namer-Core stark umbauen
- CommunityScraper direkt in Namer hineinkopieren
- Ollama als alleinige Wahrheit verwenden
- automatische Dateiänderungen ohne Validierung durchführen

---

## 2. Grundprinzip

```text
Original-Namer = Core
Eigene Erweiterungen = außen herum
Direkte Core-Änderungen = nur minimal und nur wenn wirklich nötig
```

Der Core soll möglichst updatefreundlich bleiben.

```text
ThePornDatabase/namer
        ↓
        ↓
Nanja-at-web/namer
        │
        ├── möglichst nah am Original halten
        │
        └── eigene Erweiterungen separat entwickeln
```

---

## 3. Empfohlene Architektur

```text
┌──────────────────────────────┐
│ Dateien / Medienordner        │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Namer Helper / Namer Steward  │
│ - Queue                       │
│ - Regeln                      │
│ - Vorprüfung                  │
│ - Nachprüfung                 │
│ - Review-Workflow             │
│ - API / WebUI optional        │
└────────┬──────────┬───────────┘
        │           │
        │           ▼
        │    ┌──────────────────────┐
        │    │ Ollama optional       │
        │    │ - Vorschläge          │
        │    │ - Namensanalyse       │
        │    │ - Log-Auswertung      │
        │    └──────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ Namer Core                    │
│ - bestehende Matching-Logik   │
│ - Rename-Logik                │
│ - Watchdog / CLI / WebUI      │
└────────┬──────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ Ergebnis / Review / Report    │
└──────────────────────────────┘
```

Zusätzlich kann der Helper externe oder lokale Metadatenquellen verwenden:

```text
┌──────────────────────────────┐
│ StashApp lokal                │
│ - GraphQL API                 │
│ - lokale Szenen/Tags/Studios  │
│ - lokale Scraper-Ergebnisse   │
└──────────────────────────────┘

┌──────────────────────────────┐
│ StashDB / stash-box           │
│ - Hash/Fingerprint-Matching   │
│ - Metadatenquelle             │
└──────────────────────────────┘

┌──────────────────────────────┐
│ Stash CommunityScrapers       │
│ - zusätzliche Webseitenquellen│
│ - Search by name / URL        │
│ - Fragment Scraper            │
└──────────────────────────────┘
```

---

## 4. Rollen der Komponenten

### 4.1 Namer Core

Namer bleibt zuständig für:

- bestehende Erkennung
- vorhandene Rename-Logik
- CLI-Aufrufe
- Watchdog-Funktion
- WebUI-Funktionen
- vorhandene Projektstruktur

Der Core soll nicht unnötig erweitert oder umgebaut werden.

```text
Core-Regel:
Wenn ein Feature auch außerhalb von Namer gebaut werden kann,
dann wird es außerhalb gebaut.
```

---

### 4.2 Namer Helper / Namer Steward

Der Helper ist die eigene Erweiterungsschicht.

Mögliche Aufgaben:

- Dateien überwachen
- Queue verwalten
- Namer gezielt ausführen
- Logs lesen
- Fehlerfälle sammeln
- Dry-Run-Berichte erstellen
- eigene Regeln anwenden
- Metadatenquellen abfragen
- unsichere Treffer in Review-Queue legen
- erfolgreiche Entscheidungen als lokale Regel speichern
- optionale Weboberfläche bereitstellen

Der Helper kann Namer über CLI oder Container-Aufrufe nutzen.

Beispiel:

```bash
namer rename -f "/media/input/datei.mp4"
```

oder:

```bash
python -m namer rename -f "/media/input/datei.mp4"
```

---

### 4.3 Ollama

Ollama ist optional und lokal.

Ollama soll nicht die Wahrheit bestimmen, sondern nur helfen.

Geeignete Aufgaben:

- schlechte Dateinamen analysieren
- Suchbegriffe vorschlagen
- Titelbestandteile bereinigen
- Logs erklären
- mögliche Regeln vorschlagen
- mehrere Kandidaten plausibilisieren
- Review-Texte erzeugen
- JSON-Vorschläge ausgeben

Nicht geeignet für:

- automatisches Umbenennen ohne Prüfung
- Metadaten erfinden
- Löschen oder Verschieben
- alleinige Entscheidung bei unsicheren Treffern

Empfohlene Regel:

```text
Ollama darf vorschlagen.
Der Helper entscheidet anhand von Regeln, Quellen und Confidence Score.
```

Beispiel für strukturierte Ollama-Ausgabe:

```json
{
  "cleaned_name": "Beispiel Titel",
  "search_queries": [
    "Beispiel Titel Studio 2024",
    "Studio Beispiel Titel"
  ],
  "confidence": 0.72,
  "recommended_action": "manual_review",
  "reason": "Dateiname enthält unklare Bestandteile"
}
```

---

### 4.4 StashApp

StashApp kann als lokale Metadaten- und Scraper-Zentrale dienen.

Nützliche Aufgaben:

- lokale Szenen abfragen
- vorhandene Tags, Performer und Studios lesen
- Scraper-Ergebnisse verwenden
- lokale Bibliothek als Cache nutzen
- vorhandene Metadaten mit Namer-Ergebnissen vergleichen

Empfohlene Nutzung:

```text
Namer Helper
    │
    ▼
StashApp GraphQL API
    │
    ▼
lokale Metadaten / Scraper-Ergebnisse
```

StashApp sollte nicht direkt mit Namer-Core vermischt werden.
Besser ist ein optionales Modul:

```text
modules/stash_bridge/
```

---

### 4.5 StashDB / stash-box

StashDB oder andere stash-box-Instanzen können für Matching und Metadaten hilfreich sein.

Besonders wertvoll:

- Fingerprint-/Hash-Matching
- pHash / oshash / md5 / Dauer
- Szenenmetadaten
- Studio-/Performer-Daten
- bessere Treffer bei schlechten Dateinamen

Empfohlene Reihenfolge:

```text
1. Hash/Fingerprint-Match
2. lokale StashApp-Daten
3. StashDB / stash-box Query
4. CommunityScraper
5. Ollama-Vorschlag
6. manuelle Prüfung
```

---

### 4.6 Stash CommunityScrapers

CommunityScrapers können zusätzliche Webseitenquellen erschließen.

Empfohlene Nutzung:

```text
Nicht direkt in Namer einbauen.
Stattdessen über StashApp verwenden.
```

Vorteile:

- vorhandenes Scraper-Ökosystem nutzen
- weniger eigener Wartungsaufwand
- weniger direkte Verzahnung mit Namer
- Scraper bleiben unabhängig aktualisierbar

Mögliche Scraper-Arten:

- Search by name
- Search by URL
- Fragment Scraper
- XPath-/JSON-Scraper
- Python-Scraper
- CDP-/Browser-Scraper

---

## 5. Matching-Strategie

Die Erkennung sollte stufenweise erfolgen.

```text
Neue Datei
   │
   ▼
Vorprüfung durch Helper
   │
   ▼
Namer Core normal ausführen
   │
   ├── sicherer Treffer
   │       ▼
   │   Rename erlauben
   │
   └── unsicher / kein Treffer
           ▼
      zusätzliche Quellen prüfen
           │
           ├── lokale StashApp
           ├── StashDB / stash-box
           ├── CommunityScraper
           └── Ollama optional
                   │
                   ▼
              Confidence Score
                   │
                   ├── hoch: Aktion vorschlagen oder automatisch erlauben
                   ├── mittel: Review-Queue
                   └── niedrig: manuelle Prüfung
```

---

## 6. Confidence-Modell

Jeder Treffer bekommt eine Vertrauensbewertung.

Beispiel:

| Quelle | Match-Typ | Confidence |
|---|---:|---:|
| Hash/Fingerprint exakt | sehr stark | 0.95 - 1.00 |
| StashDB/stash-box mit Dauer + Hash | stark | 0.90 - 0.98 |
| lokale StashApp-Metadaten | stark | 0.85 - 0.95 |
| URL-Scraper | gut | 0.75 - 0.90 |
| Name Search / Fragment Scraper | mittel | 0.50 - 0.80 |
| Ollama-Vorschlag | unterstützend | 0.30 - 0.75 |

Empfohlene Aktionen:

```text
>= 0.95
    automatische Aktion möglich, wenn Quelle vertrauenswürdig ist

0.75 - 0.94
    Vorschlag anzeigen, Bestätigung empfohlen

< 0.75
    manuelle Prüfung
```

Wichtig:

```text
Ollama alleine sollte nie die höchste Vertrauensstufe auslösen.
```

---

## 7. Datenschutz-Modi

Da externe Metadatenquellen genutzt werden können, sollte es klare Modi geben.

### local-only

```text
- Namer
- lokale Regeln
- lokale StashApp
- lokales Ollama
- keine externen Abfragen
```

### query-external

```text
- externe StashDB/stash-box-Abfragen erlaubt
- keine aktiven Beiträge/Uploads
- Standardmodus für viele Setups
```

### contribute

```text
- externe Abfragen erlaubt
- optionales Zurückmelden von Daten/Fingerprints
- nur bewusst aktivieren
```

Empfohlener Standard:

```text
query-external = optional aktivierbar
contribute = standardmäßig aus
```

---

## 8. Updatefreundlicher Git-Workflow

Der Fork soll möglichst nah am Original bleiben.

### Remotes

```bash
git remote add upstream https://github.com/ThePornDatabase/namer.git
git fetch upstream --tags
```

### Upstream aktualisieren

```bash
git switch main
git fetch upstream
git merge --ff-only upstream/main
git push origin main
```

### Eigene Änderungen separat halten

```bash
git switch -c feature/namer-helper-docs
```

Empfohlene Branches:

```text
main
    möglichst nah an upstream/main

feature/helper
    eigene externe Erweiterung

feature/hooks
    minimale Core-Hooks, falls nötig

nanja-release
    getestete eigene Betriebs-Version
```

---

## 9. Wann darf der Core verändert werden?

**Entscheidung 2026-05-23: Option C — Core bleibt vollständig unangetastet.**

Kein eigener Commit auf `namer/main`. Alle Erweiterungen leben im Helper oder in ProxmoxVED.

Nicht empfohlen:

```text
Matching-Core groß umbauen
Rename-Core groß umbauen
interne Datenmodelle unnötig ändern
WebUI tief verzahnen
Scraper direkt in Core kopieren
Setup-Wizard in Core einbauen
```

---

## 10. Mögliche Projektstruktur

Externe Erweiterung als eigenes Projekt:

```text
namer-helper/
├── README.md
├── docker-compose.yml
├── config/
│   ├── helper.yaml
│   ├── rules.yaml
│   └── privacy.yaml
├── src/
│   ├── main.py
│   ├── queue/
│   ├── rules/
│   ├── namer_bridge/
│   ├── stash_bridge/
│   ├── ollama_bridge/
│   ├── review/
│   └── reports/
├── docs/
│   ├── architecture.md
│   ├── update-workflow.md
│   └── matching-strategy.md
└── tests/
```

Alternative Namen:

```text
namer-helper
namer-steward
namer-assist
namer-sidecar
```

---

## 11. Docker-/Homelab-Architektur

Beispielidee:

```yaml
services:
  namer:
    image: ghcr.io/theporndatabase/namer:latest
    volumes:
      - ./config/namer:/config
      - /media:/media

  namer-helper:
    image: nanja-at-web/namer-helper:latest
    volumes:
      - ./config/helper:/config
      - /media:/media
    environment:
      - NAMER_COMMAND=python -m namer
      - STASH_URL=http://stash:9999/graphql
      - OLLAMA_BASE_URL=http://ollama:11434

  stash:
    image: stashapp/stash:latest
    volumes:
      - ./config/stash:/root/.stash
      - /media:/media

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ./ollama:/root/.ollama
```

---

## 12. Erste sinnvolle MVP-Funktionen

### MVP 1: Failed-Match-Review

```text
Namer läuft normal.
Fehlgeschlagene oder unsichere Treffer landen in einer Queue.
Helper erstellt Bericht.
```

### MVP 2: Ollama Assist

```text
Unsichere Dateinamen werden lokal analysiert.
Ollama erzeugt Suchbegriffe und Vorschläge.
Keine automatische Aktion ohne Prüfung.
```

### MVP 3: Stash Bridge

```text
Helper fragt lokale StashApp ab.
Vorhandene Metadaten werden zur Trefferbewertung genutzt.
```

### MVP 4: Rule Learning

```text
Bestätigte Entscheidungen erzeugen lokale Regeln.
```

---

## 13. Roadmap

### Phase 1: Dokumentation und Konzept ✅
- Core.md gepflegt
- Features gesammelt
- Grenzen des Core definiert
- Update-Workflow dokumentiert

### Phase 2: ProxmoxVED-Integration ✅
- ct/namer.sh angepasst
- install/namer-install.sh bereinigt
- json/namer.json aktualisiert

### Phase 3: Dokumentation einchecken ✅
- docs/core/ in namer-Fork

### Phase 4: Helper-Prototyp
- CLI-Wrapper bauen
- Namer aus Helper starten
- Logs auswerten
- Markdown-/JSON-Report erzeugen

### Phase 5: Review-Queue
- unsichere Treffer sammeln
- manuelle Entscheidung ermöglichen
- Entscheidungen speichern

### Phase 6: Ollama-Modul
- Ollama optional anbinden
- strukturierte JSON-Antworten erzwingen

### Phase 7: StashBridge
- StashApp GraphQL anbinden
- lokale Metadaten nutzen

---

## 14. Leitregeln

```text
1.  Core bleibt unangetastet.
2.  Eigene Features werden außen herum gebaut.
3.  Keine direkten Core-Patches.
4.  Deterministische Quellen vor KI.
5.  Hash/Fingerprint schlägt Dateiname.
6.  Ollama schlägt nur vor.
7.  Externe Quellen sind optional.
8.  Datenschutz-Modi müssen klar sein.
9.  Jede automatische Aktion braucht Confidence-Regeln.
10. Updates von Upstream müssen einfach bleiben.
```
