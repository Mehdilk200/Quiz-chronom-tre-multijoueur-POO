import json
import random
from pathlib import Path

from question import Question


class QuestionBank:
    """Charge et fournit les questions depuis un fichier JSON."""

    def __init__(self, path: Path):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self._data: dict[str, list[Question]] = {
            cat: [Question(q["question"], q["choices"], q["answer"]) for q in qs]
            for cat, qs in raw.items()
        }

    @property
    def categories(self) -> list[str]:
        return list(self._data)

    def draw(self, category: str, n: int) -> list[Question]:
        pool = self._data[category]
        picked: list[Question] = []
        while len(picked) < n:
            picked += random.sample(pool, min(n - len(picked), len(pool)))
        return [q.shuffled() for q in picked]