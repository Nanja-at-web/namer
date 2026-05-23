# Review: Nanja-at-web/namer

> Stand: 2026-05-22

## 1. Repository-Zweck

`Nanja-at-web/namer` ist ein Fork von `ThePornDatabase/namer`.

Namer ist ein Python-Projekt mit:

```text
- CLI
- Watchdog
- WebUI (Port 6980)
- Docker-Unterstützung
- Matching über Namen und perceptual hashes
- Rename-/Tagging-Funktionen
```

---

## 2. Branches

```text
main
codex/proxmox-setup-wizard
backup/codex-proxmox-setup-wizard-2026-05-22
```

---

## 3. Status main

```text
Nach Upstream-Update: v1.19.19
Upstream-Vergleich: 0 Commits hinter ThePornDatabase/namer:main
```

---

## 4. Status codex/proxmox-setup-wizard

```text
Branch ist 9 Commits vor main.
Enthält: Setup Wizard für Proxmox-Deployments.
```

**Entscheidung 2026-05-23:** Branch wird nicht in main gemergt.
Core bleibt unangetastet (Option C).
Branch bleibt als Archiv/Referenz erhalten.

---

## 5. Neue Dateien im Codex-Branch

### `docs/proxmox-lxc.md`
Beschreibt Debian-Proxmox-LXC-Deployment.
Wertvolles Referenzdokument — bleibt erhalten.

### `namer/mounts.py`
NFS-Probe, fstab-Generierung, sanitize-Helpers.
**Ziel:** Nicht in Namer-Core — Logik gehört in ProxmoxVED-Install-Script oder Helper.

### `namer/setup.py`
SetupPayload-Validierung, Config-Persistierung.
**Ziel:** Nicht in Namer-Core — gehört in namer-helper.

### `namer/web/routes/api.py`
Ergänzt `/api/v1/setup/*` und `/api/healthcheck`.
**Ziel:** Nicht in Namer-Core.

---

## 6. Warum nicht mergen?

```text
- widerspricht Leitprinzip: Core bleibt unangetastet
- mounts.py und setup.py sind Proxmox-spezifisch
- API-Routen für Setup-Wizard gehören nicht in Core-WebUI
- Upstream-Rebases werden aufwendiger
```

Stattdessen: Funktionalität im namer-helper aufbauen.
