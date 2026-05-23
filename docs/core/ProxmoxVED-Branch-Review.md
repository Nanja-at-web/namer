# Review: Nanja-at-web/ProxmoxVED

> Stand: 2026-05-22 / aktualisiert 2026-05-23

## 1. Repository-Zweck

`Nanja-at-web/ProxmoxVED` ist ein Fork von `community-scripts/ProxmoxVED`.

Das Repository enthält Helper-Scripts für Proxmox VE.

---

## 2. Branches

```text
main
codex/add-namer
backup/codex-add-namer-2026-05-22
```

---

## 3. Status main

```text
Nach Upstream-Update: 36 Commits nachgezogen (community-scripts/ProxmoxVED)
Stand: aktuell mit Upstream
```

---

## 4. Status codex/add-namer

```text
Branch ist 18 Commits vor main (nach Fix-Commit vom 2026-05-23).
Enthält: Namer LXC-Integration für ProxmoxVED.
```

Geänderte Dateien gegenüber main:

```text
ct/namer.sh
install/namer-install.sh
json/namer.json
```

---

## 5. Wichtige Dateien

### `ct/namer.sh`

```text
- APP="Namer"
- NAMER_UPDATE_CHANNEL=package (Standard)
- NAMER_PIP_SPEC=namer (Standard)
- var_arm64=no
- Version-Check gegen PyPI vor Update
- Stop/Backup/Restore/Start des namer-watchdog-Service
- github-channel als reservierter Platzhalter
```

### `install/namer-install.sh`

```text
- ffmpeg, nfs-common als Dependencies
- Python 3.11 via uv
- venv unter /opt/namer/.venv
- pip/uv-Installation von NAMER_PIP_SPEC
- /etc/namer/namer.cfg Bootstrap (nur upstream-kompatible Felder)
- systemd-Service namer-watchdog
- Dirs: /var/lib/namer/{watch,work,failed,dest,database}
```

### `json/namer.json`

```text
- has_arm: false
- interface_port: 6980
- documentation/website → ThePornDatabase/namer (upstream)
- 3 sachliche Notes (kein Fork-spezifischer Text)
```

---

## 6. Fixes vom 2026-05-23

| Problem | Fix |
|---|---|
| `updater["setup"][...]` → KeyError (Sektion nicht im PyPI-Package) | Wizard-Felder entfernt |
| `git` als Dependency (github-channel inaktiv) | Entfernt |
| Source-URL zeigte auf Fork | Auf upstream korrigiert |
| Fehlendes `var_arm64` | Hinzugefügt |
| Falsches Casing | Korrigiert |
| Fork-spezifische Notes und URLs | Durch neutrale Inhalte ersetzt |

---

## 7. Installations-/Update-Strategie

```text
Standard:
  NAMER_UPDATE_CHANNEL=package
  NAMER_PIP_SPEC=namer

Test (branch-spezifisch):
  NAMER_PIP_SPEC='git+https://github.com/Nanja-at-web/namer.git@branch'

Zukunft:
  NAMER_UPDATE_CHANNEL=github
  (nur wenn Namer GitHub-Releases als Asset anbietet)
```

---

## 8. Offene To-dos

```text
[ ] install/namer-install.sh in frischem Debian 13 LXC testen
[ ] systemctl status namer-watchdog prüfen
[ ] curl http://127.0.0.1:6980/ prüfen (WebUI muss in namer.cfg aktiviert werden)
[ ] Update-Funktion testen (PyPI-Version-Check + Rollback)
[ ] NFS-/Bind-Mount-Variante dokumentieren
```
