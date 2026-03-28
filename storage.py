"""
CSV-based player account storage with CRUD operations.
Follows the pattern from Python_Course_Materials CLI Project.
Uses csv.DictReader / csv.DictWriter for data persistence.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


FIELDS = ["Id", "Name", "Age", "Score"]


class PlayerStorage:
    """Persist and query player accounts stored in CSV."""

    def __init__(self, filename: str = "data.csv") -> None:
        self.filename = Path(filename)
        if not self.filename.exists():
            self._write_all([])

    # ------------------------------------------------------------------ #
    #  Low-level read / write helpers (like export_csv.py pattern)        #
    # ------------------------------------------------------------------ #

    def load_players(self) -> List[Dict[str, Any]]:
        """Load all player records from CSV and normalize types."""
        if not self.filename.exists():
            return []

        try:
            with open(self.filename, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                players: List[Dict[str, Any]] = []
                for row in reader:
                    if not row.get("Id"):
                        continue
                    try:
                        player_id = int(row["Id"])
                    except (TypeError, ValueError):
                        continue
                    name = str(row.get("Name", "Unknown")).strip() or "Unknown"
                    try:
                        age = int(row.get("Age", 0))
                    except (TypeError, ValueError):
                        age = 0
                    try:
                        score = int(row.get("Score", 0))
                    except (TypeError, ValueError):
                        score = 0
                    players.append({
                        "Id": player_id,
                        "Name": name,
                        "Age": age,
                        "Score": score,
                    })
                return players
        except (FileNotFoundError, csv.Error):
            return []

    def _write_all(self, players: List[Dict[str, Any]]) -> None:
        """Write the full player list to CSV (like export_to_csv pattern)."""
        with open(self.filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for player in players:
                writer.writerow({
                    "Id": player["Id"],
                    "Name": player["Name"],
                    "Age": player["Age"],
                    "Score": player["Score"],
                })

    def _next_id(self, players: List[Dict[str, Any]]) -> int:
        """Generate the next unique Id."""
        if not players:
            return 1
        return max(p["Id"] for p in players) + 1

    # ------------------------------------------------------------------ #
    #  CREATE                                                             #
    # ------------------------------------------------------------------ #

    def add_player(self, name: str, age: int) -> Dict[str, Any]:
        """Create a new player account and save to CSV."""
        players = self.load_players()
        new_player = {
            "Id": self._next_id(players),
            "Name": name.strip().title(),
            "Age": max(0, int(age)),
            "Score": 0,
        }
        players.append(new_player)
        self._write_all(players)
        return new_player

    # ------------------------------------------------------------------ #
    #  READ                                                               #
    # ------------------------------------------------------------------ #

    def find_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Find a single player by Id (like find_student_by_id pattern)."""
        for player in self.load_players():
            if player["Id"] == player_id:
                return player
        return None

    def find_player_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a single player by exact name (case-insensitive)."""
        lookup = name.strip().lower()
        if not lookup:
            return None
        for player in self.load_players():
            if player["Name"].lower() == lookup:
                return player
        return None

    def get_top_scores(self, n: int = 5) -> List[Dict[str, Any]]:
        """Return the highest scoring player records."""
        players = self.load_players()
        scored = [p for p in players if p["Score"] > 0]
        return sorted(scored, key=lambda p: (-p["Score"], p["Name"].lower()))[:n]

    def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Search players by partial name match."""
        search_lower = name.lower().strip()
        if not search_lower:
            return self.get_top_scores(10)
        players = self.load_players()
        matches = [p for p in players if search_lower in p["Name"].lower()]
        return sorted(matches, key=lambda p: (-p["Score"], p["Name"].lower()))

    # ------------------------------------------------------------------ #
    #  UPDATE                                                             #
    # ------------------------------------------------------------------ #

    def update_player_name(self, player_id: int, new_name: str) -> bool:
        """Update a player's name by Id."""
        new_name = new_name.strip().title()
        if not new_name:
            return False

        players = self.load_players()
        for player in players:
            if player["Id"] == player_id:
                player["Name"] = new_name
                self._write_all(players)
                return True
        return False

    def update_score(self, player_id: int, new_score: int) -> bool:
        """Update a player's score — keeps the best (highest) score."""
        players = self.load_players()
        for player in players:
            if player["Id"] == player_id:
                if new_score > player["Score"]:
                    player["Score"] = new_score
                self._write_all(players)
                return True
        return False

    # ------------------------------------------------------------------ #
    #  DELETE                                                             #
    # ------------------------------------------------------------------ #

    def delete_player(self, player_id: int) -> bool:
        """Delete a player by Id (like delete_student_by_id pattern)."""
        players = self.load_players()
        for index, player in enumerate(players):
            if player["Id"] == player_id:
                del players[index]
                self._write_all(players)
                return True
        return False

    # ------------------------------------------------------------------ #
    #  REPORT                                                             #
    # ------------------------------------------------------------------ #

    def get_report(self) -> Dict[str, Any]:
        """Generate summary information for the high scores screen."""
        players = self.load_players()
        scored = [p for p in players if p["Score"] > 0]
        if not scored:
            return {
                "total_players": len(players),
                "average": 0.0,
                "highest": 0,
                "top5": [],
            }

        total_score = sum(p["Score"] for p in scored)
        return {
            "total_players": len(players),
            "average": round(total_score / len(scored), 2),
            "highest": max(p["Score"] for p in scored),
            "top5": self.get_top_scores(5),
        }
