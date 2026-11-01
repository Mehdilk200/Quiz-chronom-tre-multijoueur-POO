import random
from dataclasses import dataclass


@dataclass
class Question:
    text: str
    choices: list[str]
    answer: int

    def shuffled(self) -> "Question":
        """Retourne une copie avec les choix mélangés."""
        order = list(range(len(self.choices)))
        random.shuffle(order)
        return Question(
            self.text,
            [self.choices[i] for i in order],
            order.index(self.answer),
        )