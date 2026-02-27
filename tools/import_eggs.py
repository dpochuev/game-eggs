#!/usr/bin/env python3
"""
Pterodactyl Egg Importer
========================
Scans all egg-*.json files in this repository and imports them into a
Pterodactyl panel, creating the required nests automatically when they
don't already exist.

Usage (environment variables):
    export PTERO_URL=https://pt.example.com
    export PTERO_API_KEY=ptla_xxxxxxxxxxxx
    python3 tools/import_eggs.py

Usage (command-line flags):
    python3 tools/import_eggs.py \
        --url https://pt.example.com \
        --api-key ptla_xxxxxxxxxxxx

Optional flags:
    --dry-run          Print what would be done without making any API calls.
    --nest-name NAME   Only import eggs that belong to the given nest name.
    --repo-root PATH   Path to the repository root (default: parent of this script).

Requirements:
    pip install requests
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required. Install it with: pip install requests", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Nest category mapping
# Maps the top-level directory name (game slug) to a nest display name.
# Keys MUST match the exact directory name on disk (case-sensitive).
# Games not listed here fall into "Custom Games".
# ---------------------------------------------------------------------------
NEST_MAP: dict[str, str] = {
    # --- Minecraft -----------------------------------------------------------
    "minecraft": "Minecraft",

    # --- Source Engine -------------------------------------------------------
    "counter_strike": "Source Engine",
    "gmod": "Source Engine",
    "half_life_2_deathmatch": "Source Engine",
    "hlds_server": "Source Engine",
    "left4dead": "Source Engine",
    "left4dead_2": "Source Engine",
    "nmrih": "Source Engine",
    "open_fortress": "Source Engine",
    "svencoop": "Source Engine",
    "team_fortress_2_classic": "Source Engine",
    "contagion": "Source Engine",
    "fof": "Source Engine",
    "sourcecoop": "Source Engine",
    "black_mesa": "Source Engine",

    # --- Steam Games ---------------------------------------------------------
    "7_days_to_die": "Steam Games",
    "Aska": "Steam Games",
    "abiotic_factor": "Steam Games",
    "aloft": "Steam Games",
    "ark_survival_ascended": "Steam Games",
    "ark_survival_evolved": "Steam Games",
    "arma": "Steam Games",
    "avorion": "Steam Games",
    "banana_shooter": "Steam Games",
    "barotrauma": "Steam Games",
    "battalion_legacy": "Steam Games",
    "citadel": "Steam Games",
    "conan_exiles": "Steam Games",
    "core_keeper": "Steam Games",
    "craftopia": "Steam Games",
    "cryofall": "Steam Games",
    "cubic_odyssey": "Steam Games",
    "dayz": "Steam Games",
    "ddnet": "Steam Games",
    "dont_starve": "Steam Games",
    "eco": "Steam Games",
    "empyrion": "Steam Games",
    "enshrouded": "Steam Games",
    "foundry": "Steam Games",
    "frozen_flame": "Steam Games",
    "holdfast": "Steam Games",
    "hurtworld": "Steam Games",
    "icarus": "Steam Games",
    "insurgency_sandstorm": "Steam Games",
    "killing_floor_2": "Steam Games",
    "longvinter": "Steam Games",
    "midnight_ghost_hunt": "Steam Games",
    "modiverse": "Steam Games",
    "mordhau": "Steam Games",
    "necesse": "Steam Games",
    "night_of_the_dead": "Steam Games",
    "no_love_lost": "Steam Games",
    "novalife_amboise": "Steam Games",
    "onset": "Steam Games",
    "operation_harsh_doorstop": "Steam Games",
    "palworld": "Steam Games",
    "pavlov_vr": "Steam Games",
    "pixark": "Steam Games",
    "plains_of_pain": "Steam Games",
    "portal_knights": "Steam Games",
    "post_scriptum": "Steam Games",
    "project_zomboid": "Steam Games",
    "quake_live": "Steam Games",
    "return_to_moria": "Steam Games",
    "rising_world": "Steam Games",
    "risk_of_rain_2": "Steam Games",
    "rust": "Steam Games",
    "satisfactory": "Steam Games",
    "scpsl": "Steam Games",
    "scum": "Steam Games",
    "smalland_survive_the_wilds": "Steam Games",
    "soldat": "Steam Games",
    "sonsoftheforest": "Steam Games",
    "soulmask": "Steam Games",
    "squad": "Steam Games",
    "starbound": "Steam Games",
    "stationeers": "Steam Games",
    "stormworks": "Steam Games",
    "subnautica_nitrox_mod": "Steam Games",
    "terratech_worlds": "Steam Games",
    "the_forest": "Steam Games",
    "the_isle": "Steam Games",
    "thefront": "Steam Games",
    "tower_unite": "Steam Games",
    "truck-simulator": "Steam Games",
    "unturned": "Steam Games",
    "v_rising": "Steam Games",
    "valheim": "Steam Games",

    # --- Space / Simulation --------------------------------------------------
    "astroneer": "Simulation Games",
    "astro_colony": "Simulation Games",
    "ksp": "Simulation Games",
    "space_engineers": "Simulation Games",

    # --- Racing --------------------------------------------------------------
    "assetto_corsa": "Racing Games",
    "automobilista2": "Racing Games",
    "trackmania": "Racing Games",

    # --- Role-Play / Social --------------------------------------------------
    "among_us": "Roleplay & Social",
    "gta": "Roleplay & Social",
    "losangelescrimes": "Roleplay & Social",
    "neosvr": "Roleplay & Social",
    "resonite": "Roleplay & Social",

    # --- Survival / Sandbox --------------------------------------------------
    "colony_survival": "Survival & Sandbox",
    "ground_breach": "Survival & Sandbox",
    "humanitz": "Survival & Sandbox",
    "rimworld": "Survival & Sandbox",
    "sunkenland": "Survival & Sandbox",
    "vintage_story": "Survival & Sandbox",
    "wurm_unlimited": "Survival & Sandbox",

    # --- Indie / Custom ------------------------------------------------------
    "Archean": "Custom Games",
    "League Sandbox": "Custom Games",
    "Nazi Zombies Portable": "Custom Games",
    "Nightingale": "Custom Games",
    "SuperTuxKart": "Custom Games",
    "americas_army": "Custom Games",
    "beamng": "Custom Games",
    "brickadia": "Custom Games",
    "classicube": "Custom Games",
    "clone_hero": "Custom Games",
    "cod": "Custom Games",
    "cs2d": "Custom Games",
    "cubeengine": "Custom Games",
    "ddracenetwork": "Custom Games",
    "dead_matter": "Custom Games",
    "doom": "Custom Games",
    "eft": "Custom Games",
    "factorio": "Custom Games",
    "fortresscraft_evolved": "Custom Games",
    "foundry_vtt": "Custom Games",
    "ftl_tachyon": "Custom Games",
    "hogwarp": "Custom Games",
    "hytale": "Custom Games",
    "just_cause": "Custom Games",
    "mindustry": "Custom Games",
    "minetest": "Custom Games",
    "mohaa": "Custom Games",
    "mount_blade_II_bannerlord": "Custom Games",
    "myth_of_empires": "Custom Games",
    "neverwinter_nights_ee": "Custom Games",
    "nuclear_option": "Custom Games",
    "openarena": "Custom Games",
    "openra": "Custom Games",
    "openrct2": "Custom Games",
    "openttd": "Custom Games",
    "path_of_titans": "Custom Games",
    "puck": "Custom Games",
    "r5reloaded": "Custom Games",
    "rdr": "Custom Games",
    "renown": "Custom Games",
    "solace_crafting": "Custom Games",
    "soldat_2": "Custom Games",
    "sonic_robo_blast_2": "Custom Games",
    "spacestation_14": "Custom Games",
    "starmade": "Custom Games",
    "swords_'n_Magic_and_Stuff": "Custom Games",
    "teeworlds": "Custom Games",
    "terraria": "Custom Games",
    "urbanterror": "Custom Games",
    "vein": "Custom Games",
    "veloren": "Custom Games",
    "voyagers_of_nera": "Custom Games",
    "wine": "Custom Games",
    "wolfenstein_enemy_territory": "Custom Games",
    "xonotic": "Custom Games",
}

DEFAULT_NEST = "Custom Games"

# Short identifier used when creating nests (lower-case, no spaces).
def _make_identifier(name: str) -> str:
    return name.lower().replace(" ", "_").replace("/", "_").replace("&", "and")


# ---------------------------------------------------------------------------
# Pterodactyl API client
# ---------------------------------------------------------------------------

class PterodactylClient:
    def __init__(self, base_url: str, api_key: str, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/application{path}"

    def _get_all(self, path: str) -> list:
        """Fetch all pages from a paginated list endpoint."""
        results = []
        page = 1
        while True:
            resp = self._session.get(self._url(path), params={"per_page": 100, "page": page})
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("data", []))
            meta = data.get("meta", {}).get("pagination", {})
            if page >= meta.get("total_pages", 1):
                break
            page += 1
        return results

    # --- Nests ---

    def list_nests(self) -> list:
        return self._get_all("/nests")

    def create_nest(self, name: str, description: str = "") -> dict:
        payload = {
            "name": name,
            "identifier": _make_identifier(name),
            "description": description,
        }
        if self.dry_run:
            print(f"  [DRY-RUN] Would create nest: {name}")
            return {"attributes": {"id": -1, "name": name}}
        resp = self._session.post(self._url("/nests"), json=payload)
        resp.raise_for_status()
        return resp.json()

    # --- Eggs ---

    def list_eggs(self, nest_id: int) -> list:
        return self._get_all(f"/nests/{nest_id}/eggs")

    def import_egg(self, nest_id: int, egg_data: dict) -> dict:
        if self.dry_run:
            print(f"  [DRY-RUN] Would import egg '{egg_data.get('name')}' into nest {nest_id}")
            return {}
        resp = self._session.post(
            self._url(f"/nests/{nest_id}/eggs/import"),
            json=egg_data,
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_eggs(repo_root: Path) -> list[tuple[str, Path]]:
    """Return list of (game_slug, egg_path) for every egg-*.json in the repo."""
    eggs = []
    for p in sorted(repo_root.rglob("egg-*.json")):
        # Skip anything inside the tools/ directory itself.
        try:
            p.relative_to(repo_root / "tools")
            continue
        except ValueError:
            pass
        # The game slug is the immediate child of repo_root.
        parts = p.relative_to(repo_root).parts
        game_slug = parts[0]
        eggs.append((game_slug, p))
    return eggs


def load_egg(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        print(f"  WARNING: Could not parse {path}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    client = PterodactylClient(args.url, args.api_key, dry_run=args.dry_run)

    if args.dry_run:
        print("=== DRY-RUN MODE — no changes will be made ===\n")

    # 1. Discover eggs
    print("Scanning repository for eggs …")
    all_eggs = find_eggs(repo_root)
    print(f"  Found {len(all_eggs)} egg file(s).\n")

    # 2. Build nest → [egg_path] mapping
    nest_to_eggs: dict[str, list[tuple[str, Path]]] = {}
    for slug, path in all_eggs:
        nest_name = NEST_MAP.get(slug, DEFAULT_NEST)
        if args.nest_name and nest_name != args.nest_name:
            continue
        nest_to_eggs.setdefault(nest_name, []).append((slug, path))

    if not nest_to_eggs:
        print("No eggs matched the given filter.")
        return 0

    # 3. Fetch existing nests
    print("Fetching existing nests from panel …")
    try:
        existing_nests = client.list_nests()
    except (requests.HTTPError, requests.ConnectionError, requests.exceptions.RequestException) as exc:
        if args.dry_run:
            print(f"  WARNING: Could not reach panel ({exc}); assuming no nests exist yet.")
            existing_nests = []
        else:
            print(f"ERROR: Could not fetch nests: {exc}", file=sys.stderr)
            return 1

    nest_by_name: dict[str, int] = {
        n["attributes"]["name"]: n["attributes"]["id"] for n in existing_nests
    }
    print(f"  Found {len(nest_by_name)} existing nest(s): {', '.join(nest_by_name) or '(none)'}\n")

    # 4. Create missing nests and import eggs
    total_imported = 0
    total_skipped = 0
    total_failed = 0

    for nest_name, egg_list in sorted(nest_to_eggs.items()):
        print(f"── Nest: {nest_name} ({len(egg_list)} egg(s)) ──")

        # Create nest if missing
        if nest_name not in nest_by_name:
            print(f"  Creating nest '{nest_name}' …")
            try:
                result = client.create_nest(nest_name, description=f"{nest_name} — auto-created by import_eggs.py")
                nest_id = result["attributes"]["id"]
                nest_by_name[nest_name] = nest_id
                print(f"  Created nest with id={nest_id}")
            except (requests.HTTPError, requests.exceptions.RequestException) as exc:
                print(f"  ERROR: Could not create nest '{nest_name}': {exc}", file=sys.stderr)
                total_failed += len(egg_list)
                continue
        else:
            nest_id = nest_by_name[nest_name]

        # Fetch eggs already in this nest so we can skip duplicates by name.
        existing_egg_names: set[str] = set()
        if not args.dry_run and nest_id != -1:
            try:
                ex = client.list_eggs(nest_id)
                existing_egg_names = {e["attributes"]["name"] for e in ex}
            except (requests.HTTPError, requests.exceptions.RequestException):
                pass  # not fatal – we'll just try to import everything

        # Import each egg
        for slug, path in egg_list:
            egg_data = load_egg(path)
            if egg_data is None:
                total_failed += 1
                continue

            egg_name = egg_data.get("name", path.stem)

            if egg_name in existing_egg_names:
                print(f"  SKIP  {egg_name}  (already exists)")
                total_skipped += 1
                continue

            print(f"  → Importing '{egg_name}' from {path.relative_to(repo_root)} …", end="", flush=True)
            try:
                client.import_egg(nest_id, egg_data)
                existing_egg_names.add(egg_name)
                print(" OK")
                total_imported += 1
                # Small delay to avoid rate-limiting
                if not args.dry_run:
                    time.sleep(0.3)
            except requests.HTTPError as exc:
                body = ""
                if exc.response is not None:
                    try:
                        body = exc.response.json()
                    except Exception:
                        body = exc.response.text[:200]
                print(f" FAILED\n    {exc}\n    {body}", file=sys.stderr)
                total_failed += 1

        print()

    # 5. Summary
    print("=" * 50)
    print(f"Imported : {total_imported}")
    print(f"Skipped  : {total_skipped}  (already existed)")
    print(f"Failed   : {total_failed}")
    return 0 if total_failed == 0 else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import all game eggs from this repository into a Pterodactyl panel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("PTERO_URL", ""),
        help="Base URL of your Pterodactyl panel (env: PTERO_URL)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("PTERO_API_KEY", ""),
        help="Application API key (env: PTERO_API_KEY). Never pass this in plain shell history.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making any API calls.",
    )
    parser.add_argument(
        "--nest-name",
        default="",
        help="Only import eggs belonging to this nest (e.g. 'Minecraft').",
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Path to the repository root (default: parent of tools/).",
    )

    args = parser.parse_args()

    if not args.url:
        parser.error("Panel URL is required (--url or PTERO_URL env var).")
    if not args.api_key:
        parser.error("API key is required (--api-key or PTERO_API_KEY env var).")

    sys.exit(run(args))


if __name__ == "__main__":
    main()
