# Branch-, Update-, Commit- und History-Workflow

## 1. Grundregeln

```text
main     = möglichst nahe an Upstream, kein eigener Code
docs/*   = reine Dokumentation
feature/ = eigene gezielte Feature-Branches (nur im Helper)
backup/* = Sicherung vor Rebase/Merge
```

Nicht direkt auf `main` experimentieren.
Kein eigener Feature-Code auf `namer/main` — Core bleibt Upstream.

---

## 2. Upstream-Remotes setzen

### Namer

```bash
cd /projects/Namer
git remote -v
git remote add upstream https://github.com/ThePornDatabase/namer.git
git fetch upstream --prune --tags
```

### ProxmoxVED

```bash
cd /projects/ProxmoxVED
git remote add upstream https://github.com/community-scripts/ProxmoxVED.git
git fetch upstream --prune --tags
```

Wenn `upstream` schon existiert:

```bash
git remote set-url upstream <URL>
git fetch upstream --prune --tags
```

---

## 3. SSH statt HTTPS für origin

```bash
# Namer
git remote set-url origin git@github.com:Nanja-at-web/namer.git

# ProxmoxVED
git remote set-url origin git@github.com:Nanja-at-web/ProxmoxVED.git
```

SSH-Test:

```bash
ssh -T git@github.com
# Erwartet: Hi Nanja-at-web! You've successfully authenticated...
```

---

## 4. Main sauber aktualisieren

```bash
git switch main
git fetch upstream --prune --tags
git merge --ff-only upstream/main
git push origin main
```

Wenn `--ff-only` fehlschlägt:

```text
Nicht blind mergen.
Erst prüfen, ob eigene Commits auf main liegen.
```

Prüfen:

```bash
git log --oneline upstream/main..main
git log --oneline main..upstream/main
```

---

## 5. Branch vor Rebase sichern

### Namer

```bash
git branch backup/codex-proxmox-setup-wizard-DATUM origin/codex/proxmox-setup-wizard
git push origin backup/codex-proxmox-setup-wizard-DATUM
```

### ProxmoxVED

```bash
git branch backup/codex-add-namer-DATUM origin/codex/add-namer
git push origin backup/codex-add-namer-DATUM
```

---

## 6. Codex-Branch rebasen

```bash
git switch codex/add-namer
git rebase main
```

Wenn Konflikte entstehen:

```bash
git status
git diff
# Konflikte lösen
git add <datei>
git rebase --continue
```

Abbruch:

```bash
git rebase --abort
```

---

## 7. Keine großen Misch-Merges

Nicht:

```bash
git switch main
git merge codex/add-namer
```

Besser:

```text
- Themen trennen
- kleine Commits
- Doku separat
- Tests separat
- ProxmoxVED-Integration separat
```

---

## 8. Commit-Regeln

```bash
git commit -m "docs: add core extension strategy"
git commit -m "docs: document namer proxmox lxc workflow"
git commit -m "feat(proxmoxved): add namer lxc helper script"
git commit -m "fix(namer): align install script with upstream"
git commit -m "test(namer): add setup payload validation tests"
```

---

## 9. Vor jedem Push

```bash
git status
git fetch upstream --prune
git log --oneline --decorate --graph --all -n 20
git diff --stat main..HEAD
```

Checkliste:

```text
[ ] main aktuell?
[ ] Branch gesichert?
[ ] Diff verstanden?
[ ] Keine Secrets / Token?
[ ] Keine lokalen Pfade hardcoded?
[ ] Core wirklich nötig verändert? (Antwort soll "Nein" sein)
```

---

## 10. Push-Befehle

```bash
# Namer
cd /projects/Namer
git push origin main
git push --force-with-lease origin codex/proxmox-setup-wizard
git push origin backup/codex-proxmox-setup-wizard-2026-05-22

# ProxmoxVED
cd /projects/ProxmoxVED
git push origin main
git push --force-with-lease origin codex/add-namer
git push origin backup/codex-add-namer-2026-05-22
```
