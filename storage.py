import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ScoreStorage:
    """Persist and query high score records stored in JSON."""

    def __init__(self, filename: str = "data.json") -> None:
        self.filename = Path(filename)
        if not self.filename.exists():
            self.save_all_scores([])

    def load_scores(self) -> List[Dict[str, Any]]:
        """Load scores and normalize malformed records."""
        try:
            raw_scores = json.loads(self.filename.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        cleaned_scores: List[Dict[str, Any]] = []
        for item in raw_scores:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "Unknown Player")).strip() or "Unknown Player"
            score = item.get("score", 0)
            try:
                parsed_score = int(score)
            except (TypeError, ValueError):
                parsed_score = 0
            cleaned_scores.append({"name": name, "score": parsed_score})
        return cleaned_scores

    def save_all_scores(self, scores: List[Dict[str, Any]]) -> None:
        """Save a normalized score list to disk."""
        normalized = [
            {
                "name": str(score.get("name", "Unknown Player")).strip() or "Unknown Player",
                "score": max(0, int(score.get("score", 0))),
            }
            for score in scores
        ]
        self.filename.write_text(
            json.dumps(normalized, indent=4),
            encoding="utf-8",
        )

    def add_new_score(self, name: str, score: int) -> Dict[str, Any]:
        """Create and store a new score record."""
        record = {
            "name": name.strip() or "Unknown Player",
            "score": max(0, int(score)),
        }
        scores = self.load_scores()
        scores.append(record)
        self.save_all_scores(scores)
        return record

    def get_top_scores(self, n: int = 5) -> List[Dict[str, Any]]:
        """Return the highest scoring records."""
        scores = self.load_scores()
        return sorted(scores, key=lambda item: (-item["score"], item["name"].lower()))[:n]

    def delete_all_records(self) -> None:
        """Clear all saved scores."""
        self.save_all_scores([])

    def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Search scores by partial player name."""
        search_lower = name.lower().strip()
        if not search_lower:
            return self.get_top_scores(10)

        scores = self.load_scores()
        matches = [score for score in scores if search_lower in score["name"].lower()]
        return sorted(matches, key=lambda item: (-item["score"], item["name"].lower()))

    def update_score(
        self,
        old_name: str,
        new_name: Optional[str] = None,
        new_score: Optional[int] = None,
    ) -> bool:
        """Update the first matching score entry."""
        lookup_name = old_name.strip().lower()
        if not lookup_name:
            return False

        scores = self.load_scores()
        updated = False
        for score in scores:
            if score["name"].lower() != lookup_name:
                continue
            if new_name is not None and new_name.strip():
                score["name"] = new_name.strip()
            if new_score is not None:
                score["score"] = max(0, int(new_score))
            updated = True
            break

        if updated:
            self.save_all_scores(scores)
        return updated

    def delete_score(self, name: str) -> bool:
        """Delete the first matching score entry."""
        lookup_name = name.strip().lower()
        if not lookup_name:
            return False

        scores = self.load_scores()
        for index, score in enumerate(scores):
            if score["name"].lower() == lookup_name:
                del scores[index]
                self.save_all_scores(scores)
                return True
        return False

    def get_report(self) -> Dict[str, Any]:
        """Generate summary information for the score screen."""
        scores = self.load_scores()
        if not scores:
            return {
                "total_players": 0,
                "average": 0.0,
                "highest": 0,
                "top5": [],
            }

        total_score = sum(score["score"] for score in scores)
        return {
            "total_players": len(scores),
            "average": round(total_score / len(scores), 2),
            "highest": max(score["score"] for score in scores),
            "top5": self.get_top_scores(5),
        }
