import json
import os
from typing import List, Dict, Optional, Any

class ScoreStorage:
    """Storage class for high scores JSON persistence.
    Supports full CRUD: Create, Read, Update, Delete.
    Search by name, reports (avg, top5)."""
    
    def __init__(self, filename: str = "data.json") -> None:
        self.filename = filename
        if not os.path.exists(self.filename):
            self.save_all_scores([])

    def load_scores(self) -> List[Dict[str, Any]]:
        """Load all scores from JSON file."""
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_all_scores(self, scores: List[Dict[str, Any]]) -> None:
        """Save entire scores list to JSON."""
        with open(self.filename, 'w') as file:
            json.dump(scores, file, indent=4)

    def add_new_score(self, name: str, score: int) -> None:
        """CRUD Create: Add new score entry."""
        if not name or not name.strip():
            name = "Unknown Player"
        scores = self.load_scores()
        scores.append({"name": name.strip(), "score": score})
        self.save_all_scores(scores)

    def get_top_scores(self, n: int = 5) -> List[Dict[str, int]]:
        """Get top N scores sorted descending."""
        scores = self.load_scores()
        return sorted(scores, key=lambda x: x['score'], reverse=True)[:n]

    def delete_all_records(self) -> None:
        """CRUD Delete: Clear all records."""
        self.save_all_scores([])

    def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Search/Filter scores by partial name match (case insensitive)."""
        scores = self.load_scores()
        search_lower = name.lower().strip()
        return [s for s in scores if search_lower in s['name'].lower()]

    def update_score(self, old_name: str, new_name: Optional[str] = None, new_score: Optional[int] = None) -> bool:
        """CRUD Update: Update name and/or score by old name."""
        scores = self.load_scores()
        updated = False
        for s in scores:
            if s['name'].lower() == old_name.lower():
                if new_name:
                    s['name'] = new_name.strip()
                if new_score is not None:
                    s['score'] = new_score
                updated = True
                break  # First match
        if updated:
            self.save_all_scores(scores)
        return updated

    def delete_score(self, name: str) -> bool:
        """CRUD Delete: Delete first matching score by name."""
        scores = self.load_scores()
        initial_len = len(scores)
        scores = [s for s in scores if s['name'].lower() != name.lower()]
        if len(scores) < initial_len:
            self.save_all_scores(scores)
            return True
        return False

    def get_report(self) -> Dict[str, Any]:
        """Generate report: average score, top 5."""
        scores = self.load_scores()
        if not scores:
            return {'average': 0.0, 'top5': []}
        avg = sum(s['score'] for s in scores) / len(scores)
        return {'average': round(avg, 2), 'top5': self.get_top_scores(5)}

