import json
import os
from datetime import datetime


RARITY_ORDER = ["MYTHIC", "LEGENDARY", "EPIC", "RARE", "COMMON"]

_SESSION_FILE = os.path.join(os.path.dirname(__file__), "..", "detected_skins.json")


class DetectedSkin:
    def __init__(self, skin_entry: dict, first_seen: str):
        self.full_name = skin_entry["full_name"]
        self.name = skin_entry["name"]
        self.weapon = skin_entry["weapon"]
        self.build = skin_entry.get("build", "")
        self.rarity = skin_entry.get("rarity", "COMMON")
        self.cost = skin_entry.get("cost", 0)
        self.source = skin_entry.get("source", "")
        self.obtainable = skin_entry.get("obtainable", True)
        self.season = skin_entry.get("season")
        self.first_seen = first_seen

    def to_dict(self) -> dict:
        return {
            "full_name": self.full_name,
            "name": self.name,
            "weapon": self.weapon,
            "build": self.build,
            "rarity": self.rarity,
            "cost": self.cost,
            "source": self.source,
            "obtainable": self.obtainable,
            "season": self.season,
            "first_seen": self.first_seen,
        }


class SkinStorage:
    def __init__(self, session_path: str = None):
        self.session_path = os.path.abspath(session_path or _SESSION_FILE)
        self._detected: dict[str, DetectedSkin] = {}

    def add(self, skin_entry: dict) -> bool:
        """
        Add a detected skin. Returns True if newly added, False if already known.
        """
        full_name = skin_entry.get("full_name", "")
        if not full_name or full_name in self._detected:
            return False
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._detected[full_name] = DetectedSkin(skin_entry, timestamp)
        self._save()
        return True

    def get_all(self) -> list[DetectedSkin]:
        return sorted(
            self._detected.values(),
            key=lambda s: (RARITY_ORDER.index(s.rarity) if s.rarity in RARITY_ORDER else 99, s.weapon, s.name)
        )

    def clear(self):
        self._detected = {}
        if os.path.isfile(self.session_path):
            os.remove(self.session_path)

    def count(self) -> int:
        return len(self._detected)

    def count_by_rarity(self) -> dict[str, int]:
        counts = {r: 0 for r in RARITY_ORDER}
        for s in self._detected.values():
            if s.rarity in counts:
                counts[s.rarity] += 1
        return counts

    def load_session(self):
        """Restore previously saved session if it exists."""
        if not os.path.isfile(self.session_path):
            return
        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data:
                full_name = entry.get("full_name", "")
                if full_name and full_name not in self._detected:
                    self._detected[full_name] = DetectedSkin(entry, entry.get("first_seen", ""))
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self):
        try:
            with open(self.session_path, "w", encoding="utf-8") as f:
                json.dump([s.to_dict() for s in self._detected.values()], f, indent=2, ensure_ascii=False)
        except OSError:
            pass
