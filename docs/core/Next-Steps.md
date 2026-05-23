# Nächste Schritte

## Status

| Phase | Inhalt | Status |
|---|---|---|
| Phase 0 | Git-Hygiene (Upstream, Rebases, Backups, SSH, Push) | ✅ abgeschlossen |
| Phase 1 | Architektur-Entscheidung: Core bleibt unangetastet (Option C) | ✅ abgeschlossen |
| Phase 2 | ProxmoxVED codex/add-namer bereinigt und gepusht | ✅ abgeschlossen |
| Phase 3 | Dokumentation in docs/core/ eingecheckt | ✅ abgeschlossen |
| Phase 4 | namer-helper als eigenes Projekt aufsetzen | 🔜 nächster Schritt |
| Phase 5 | Review-Queue im Helper | ⬜ geplant |
| Phase 6 | Ollama-Modul | ⬜ geplant |
| Phase 7 | StashBridge | ⬜ geplant |

---

## Phase 4: namer-helper aufsetzen

### Projektstruktur

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
└── tests/
```

### MVP-Reihenfolge

**MVP 1 — Failed-Match-Review (kein KI, kein Stash)**

```text
- Namer-Log auslesen
- betroffene Dateien sammeln
- JSON-/Markdown-Report erzeugen
- manuelle Entscheidung vorbereiten
```

**MVP 2 — Ollama Assist**

```text
- Dateiname bereinigen
- Suchvarianten erzeugen
- Confidence-Vorschlag
- keine automatische Aktion
```

**MVP 3 — Stash Bridge**

```text
- lokale StashApp GraphQL abfragen
- Stash-Ergebnis mit Namer-Ergebnis vergleichen
```

**MVP 4 — Rule Learning**

```text
- bestätigte Entscheidungen als lokale YAML-Regeln speichern
```

---

## Offene Fragen

```text
[ ] Soll namer-helper als eigenes GitHub-Repo entstehen?
[ ] Oder zunächst als Unterverzeichnis in Nanja-at-web/namer?
[ ] Welche Sprache für den Helper? Python empfohlen (passt zu Namer-Ökosystem)
[ ] Soll StashApp Pflicht, optional oder späterer Ausbau sein?
[ ] Soll Ollama nur Reports erstellen oder auch Vorschläge in Review-Queue schreiben?
```

---

## ProxmoxVED: Noch zu testen

```bash
# LXC erstellen mit ct/namer.sh
# Dann im Container:
systemctl status namer-watchdog
journalctl -u namer-watchdog -n 50 --no-pager

# namer.cfg anpassen (porndb_token, web = True)
# Dann:
systemctl restart namer-watchdog
curl http://127.0.0.1:6980/
```
