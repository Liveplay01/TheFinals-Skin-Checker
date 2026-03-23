"""
Wiki scraper for The Finals weapon skin data.
Attempts to scrape https://www.thefinals.wiki and update skin_db.json.

Run standalone:  python -m data.scraper
"""

import json
import os
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

SKIN_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "skin_db.json")

BASE_URL = "https://www.thefinals.wiki"
WEAPONS_URL = f"{BASE_URL}/wiki/Weapons"

# Weapons list with build classification
WEAPONS = {
    "Light": [
        "93R", "ARN-220", "Dagger", "LH1", "M11", "M26 Matter",
        "Recurve Bow", "SH1900", "SR-84", "Sword", "Throwing Knives", "V9S", "XP-54",
    ],
    "Medium": [
        "AKM", "CB-01 Repeater", "Cerberus 12GA", "CL-40", "Dual Blades",
        "FAMAS", "FCAR", "Model 1887", "P90", "Pike-556", "R.357", "Riot Shield",
    ],
    "Heavy": [
        ".50 Akimbo", "BFR Titan", "Flamethrower", "KS-23", "Lewis Gun",
        "M134 Minigun", "M60", "MGL32", "SA1216", "ShAK-50", "Sledgehammer", "Spear",
    ],
}

RARITY_KEYWORDS = {
    "MYTHIC": ["mythic"],
    "LEGENDARY": ["legendary"],
    "EPIC": ["epic"],
    "RARE": ["rare"],
    "COMMON": ["common"],
}

SOURCE_KEYWORDS = {
    "Battle Pass": ["battle pass", "battlepass"],
    "Special Pass": ["special pass"],
    "Event": ["event", "limited time", "seasonal"],
    "Ranked": ["ranked"],
    "Store": ["store", "multibucks", "shop"],
    "Default": ["default", "base"],
}

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "TheFinalsStats-Scraper/1.0 (educational skin tracker)"
})


def _get_weapon_slug(weapon_name: str) -> str:
    return weapon_name.replace(" ", "_").replace(".", "").replace("-", "-")


def _infer_rarity(text: str) -> str:
    text_lower = text.lower()
    for rarity, keywords in RARITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return rarity
    return "COMMON"


def _infer_source(text: str) -> str:
    text_lower = text.lower()
    for source, keywords in SOURCE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return source
    return "Store"


def _extract_cost(text: str) -> int:
    numbers = re.findall(r"\b(\d{2,5})\b", text)
    if numbers:
        return int(numbers[0])
    return 0


def scrape_weapon_page(weapon_name: str, build: str) -> list[dict]:
    """Scrape skin entries from a weapon's wiki page."""
    slug = _get_weapon_slug(weapon_name)
    url = f"{BASE_URL}/wiki/{slug}"
    skins = []

    try:
        resp = SESSION.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"  [!] {weapon_name}: HTTP {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for skin-related tables or sections
        skin_tables = soup.find_all("table", class_=re.compile(r"skin|cosmetic|weapon", re.I))
        if not skin_tables:
            skin_tables = soup.find_all("table")

        for table in skin_tables:
            rows = table.find_all("tr")
            headers = []
            for i, row in enumerate(rows):
                cols = [th.get_text(strip=True) for th in row.find_all(["th", "td"])]
                if i == 0:
                    headers = [c.lower() for c in cols]
                    continue
                if not cols:
                    continue

                skin_name = cols[0] if cols else ""
                if not skin_name or len(skin_name) < 2:
                    continue

                row_text = " ".join(cols)
                rarity = _infer_rarity(row_text)
                source = _infer_source(row_text)
                cost = _extract_cost(row_text)

                skin_id = f"{slug.lower()}_{skin_name.lower().replace(' ', '_')}"
                full_name = f"{weapon_name} {skin_name}"

                skins.append({
                    "id": skin_id,
                    "name": skin_name,
                    "weapon": weapon_name,
                    "build": build,
                    "full_name": full_name,
                    "rarity": rarity,
                    "cost": cost,
                    "source": source,
                    "season": None,
                    "obtainable": rarity in ("COMMON", "RARE"),
                })

        if skins:
            print(f"  [+] {weapon_name}: found {len(skins)} skin(s)")
        else:
            # At minimum add a Default entry
            skins.append({
                "id": f"{slug.lower()}_default",
                "name": "Default",
                "weapon": weapon_name,
                "build": build,
                "full_name": f"{weapon_name} Default",
                "rarity": "COMMON",
                "cost": 0,
                "source": "Default",
                "season": None,
                "obtainable": True,
            })
            print(f"  [-] {weapon_name}: no table found, added Default only")

    except requests.RequestException as exc:
        print(f"  [!] {weapon_name}: request failed — {exc}")

    return skins


def run_scraper(db_path: str = None, progress_callback=None) -> tuple[bool, str]:
    """
    Scrapes the wiki and updates skin_db.json.
    Returns (success: bool, message: str).
    """
    path = os.path.abspath(db_path or SKIN_DB_PATH)
    print("Starting wiki scraper...")

    # Load existing DB to preserve manually added entries
    existing = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        for entry in old_data.get("skins", []):
            existing[entry["id"]] = entry
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    all_skins = {}
    total = sum(len(v) for v in WEAPONS.values())
    done = 0

    for build, weapons in WEAPONS.items():
        for weapon_name in weapons:
            done += 1
            if progress_callback:
                progress_callback(done, total, weapon_name)
            scraped = scrape_weapon_page(weapon_name, build)
            for entry in scraped:
                skin_id = entry["id"]
                # Prefer existing manual entries over scraped ones
                if skin_id not in existing:
                    all_skins[skin_id] = entry
                else:
                    all_skins[skin_id] = existing[skin_id]

    # Merge any remaining manual entries not overwritten
    for skin_id, entry in existing.items():
        if skin_id not in all_skins:
            all_skins[skin_id] = entry

    db = {
        "version": "1.1",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "note": "Updated by wiki scraper. Edit skin_db.json manually to add custom entries.",
        "skins": list(all_skins.values()),
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        msg = f"Done. {len(all_skins)} skins saved to {path}"
        print(msg)
        return True, msg
    except OSError as exc:
        msg = f"Failed to write database: {exc}"
        print(msg)
        return False, msg


if __name__ == "__main__":
    success, message = run_scraper()
    sys.exit(0 if success else 1)
