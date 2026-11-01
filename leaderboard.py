import json
from pathlib import Path

from player import Player


class Leaderboard:
    def __init__(self, path: Path):
        self.path = path
        self.data: dict[str, dict[str, int]] = {}
        if path.exists():
            try:
                self.data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.data = {}

    def record(self, players: list[Player]) -> None:
        best = max(p.score for p in players)
        for p in players:
            entry = self.data.setdefault(p.name, {"total": 0, "games": 0, "wins": 0})
            entry["total"] += p.score
            entry["games"] += 1
            entry["wins"] += int(p.score == best)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    def show(self, top: int = 10) -> None:
        print("\n🏆  CLASSEMENT GÉNÉRAL")
        print(f"{'#':<3}{'Joueur':<15}{'Points':>8}{'Parties':>9}{'Victoires':>11}")
        ranking = sorted(self.data.items(), key=lambda kv: kv[1]["total"], reverse=True)
        for i, (name, s) in enumerate(ranking[:top], 1):
            print(f"{i:<3}{name:<15}{s['total']:>8}{s['games']:>9}{s['wins']:>11}")