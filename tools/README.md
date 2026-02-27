# Tools

Utility scripts for managing this repository.

---

## `import_eggs.py` — Pterodactyl Egg Importer

Imports all `egg-*.json` files from this repository into a Pterodactyl panel.
It automatically creates any missing nests, grouping games into sensible
categories (Minecraft, Steam Games, Source Engine, Simulation Games, etc.).

### Requirements

```
pip install requests
```

### Usage

Pass the panel URL and Application API key either as environment variables
(recommended — keeps secrets out of your shell history):

```bash
export PTERO_URL="https://your.panel.example.com"
export PTERO_API_KEY="ptla_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

python3 tools/import_eggs.py
```

or as command-line flags:

```bash
python3 tools/import_eggs.py \
    --url https://your.panel.example.com \
    --api-key ptla_xxxx
```

### Options

| Flag | Env var | Description |
|---|---|---|
| `--url URL` | `PTERO_URL` | Base URL of the Pterodactyl panel (required) |
| `--api-key KEY` | `PTERO_API_KEY` | Application API key with full access (required) |
| `--dry-run` | — | Print what would happen without calling the API |
| `--nest-name NAME` | — | Only import eggs in the named nest (e.g. `Minecraft`) |
| `--repo-root PATH` | — | Override the repository root path |

### Generating an Application API key

1. Log in to your Pterodactyl panel as an administrator.
2. Go to **Admin → Application API**.
3. Click **Create New** and grant it full read/write access.
4. Copy the key shown — you won't see it again.

### Nest categories

| Nest | Games |
|---|---|
| Minecraft | All Minecraft variants (Paper, Forge, Fabric, …) |
| Steam Games | ARK, Rust, Valheim, CS:GO, DayZ, Palworld, and most other Steam titles |
| Source Engine | CS 1.6, CS2, Garry's Mod, Left 4 Dead, TF2 Classic, … |
| Simulation Games | Astroneer, KSP, Space Engineers |
| Racing Games | Assetto Corsa, Automobilista 2, Trackmania |
| Roleplay & Social | GTA FiveM / RAGE-MP, Among Us, VRChat alternatives |
| Survival & Sandbox | Colony Survival, Vintage Story, RimWorld, … |
| Custom Games | Everything else |

Games not listed in the internal category map fall into **Custom Games**.

### Notes

* **Duplicate eggs** (same name already present in the target nest) are
  skipped automatically.
* The script inserts a short delay (0.3 s) between imports to avoid
  triggering rate-limiting on the panel.
* The script requires Pterodactyl **≥ 1.6** — the
  `/api/application/nests/{id}/eggs/import` endpoint was introduced there.
