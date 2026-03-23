import json
import os


_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "skin_db.json")


class SkinDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = os.path.abspath(db_path or _DB_PATH)
        self._skins: dict[str, dict] = {}  # full_name → skin entry
        self._names: list[str] = []
        self.version = "unknown"
        self.last_updated = "unknown"
        self.load()

    def load(self):
        """Load skin_db.json from disk."""
        if not os.path.isfile(self.db_path):
            raise FileNotFoundError(f"Skin database not found: {self.db_path}")
        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.version = data.get("version", "unknown")
        self.last_updated = data.get("last_updated", "unknown")
        self._skins = {}
        for entry in data.get("skins", []):
            full_name = entry.get("full_name", "")
            if full_name:
                self._skins[full_name] = entry
        self._names = list(self._skins.keys())

    def reload(self):
        """Reload database from disk (after scraper update)."""
        self.load()

    def get_skin(self, full_name: str) -> dict | None:
        return self._skins.get(full_name)

    def get_all_names(self) -> list[str]:
        return self._names

    def get_all_skins(self) -> list[dict]:
        return list(self._skins.values())

    def count(self) -> int:
        return len(self._skins)

    def get_skins_by_rarity(self, rarity: str) -> list[dict]:
        return [s for s in self._skins.values() if s.get("rarity") == rarity]

    def get_skins_by_weapon(self, weapon: str) -> list[dict]:
        return [s for s in self._skins.values() if s.get("weapon", "").lower() == weapon.lower()]
