# Proxmox LXC Deployment Draft

This repository includes a draft handoff artifact set for a Proxmox VE LXC deployment of `namer`. It is intentionally LXC-focused and NFS-oriented, and it is meant to support a later upstream handoff rather than act as a finished `community-scripts/ProxmoxVED` contribution.

## What is included

- `contrib/proxmoxved/ct/namer.sh`
- `contrib/proxmoxved/install/namer-install.sh`

The split mirrors the upstream handoff shape:

- `ct/namer.sh` is the wrapper artifact that documents container assumptions and points at the installer.
- `install/namer-install.sh` is the draft in-container bootstrapper.

## Intended deployment flow

1. Create a Debian-based Proxmox LXC for `namer`, not a full VM.
2. Run the draft installer inside the container.
3. Let the installer add Python, `ffmpeg`, and `nfs-common`, then install `namer` into `/opt/namer/venv`.
   The default package source is PyPI, which fits a more stable ProxmoxVED-style install/update flow.
   For handoff validation against this repo state, override the package source before running it, for example:
   `NAMER_PIP_SPEC='git+https://github.com/Nanja-at-web/namer.git' ./namer-install.sh`
4. The installer seeds `/etc/namer/namer.cfg` with web mode enabled and local bootstrap directories under `/var/lib/namer`, so the setup UI is reachable before NAS mounts are finalized.
   That config file is also handed to the `namer` service user with write access so the setup wizard can persist its changes.
5. Start `namer` with `NAMER_CONFIG=/etc/namer/namer.cfg`.
6. Open the web UI and complete the first-boot setup wizard.
7. Enter the TPDB token, NFS host/share, and the final watchdog directories.
8. Confirm the final NFS mount behavior and persist it only after the wizard values are validated.

## Recommended container shape

- OS: Debian 13 / Trixie
- Workload type: LXC
- CPU: 2 cores
- Memory: 2 GiB
- Root disk: 8 GiB minimum
- Network: bridge mode with access to the NAS export

## Directory model

The draft assumes:

- NAS mount path: `/mnt/nas`
- Local bootstrap watch path: `/var/lib/namer/watch`
- Local work path: `/var/lib/namer/work`
- Local failed path: `/var/lib/namer/failed`
- Local bootstrap dest path: `/var/lib/namer/dest`

Bootstrap values written by the installer:

- `watch_dir = /var/lib/namer/watch`
- `work_dir = /var/lib/namer/work`
- `failed_dir = /var/lib/namer/failed`
- `dest_dir = /var/lib/namer/dest`
- `web = True`

Typical final wizard values after NAS validation:

- `watch_dir = /mnt/nas/watch`
- `work_dir = /var/lib/namer/work`
- `failed_dir = /var/lib/namer/failed`
- `dest_dir = /mnt/nas/dest`

That keeps the media-facing paths on NFS while leaving transient work queues local to the container filesystem.

## NFS-first setup notes

- Keep the deployment centered on a NAS-backed share, not on a VM-attached virtual disk layout.
- For Proxmox deployments, prefer a host-mounted and bind-mounted NAS path when possible instead of relying on an in-container mount as the primary model.
- The setup wizard's in-container NFS probe can fail even when the final Proxmox host mount and bind mount layout is correct.
- Validate network reachability and mount options from inside the LXC before enabling persistent mounts.
- If you need different mount options, update them in the setup wizard data and in your eventual `/etc/fstab` entry together.

## Handoff status

This artifact set is intentionally conservative:

- It documents the intended Proxmox LXC flow.
- It gives a draft wrapper plus installer for future upstream adaptation.
- It does not claim to satisfy upstream `community-scripts` review rules yet.

Use it as a starting point for the handoff, not as a published ProxmoxVE installer.

## Update strategy

- Default install/update source: PyPI (`namer`)
- Local/fork validation override: `NAMER_PIP_SPEC=...`
- Installed version file: `/opt/namer_version.txt`

That split keeps the upstream path conservative while still letting you validate unpublished changes from GitHub during handoff work.
