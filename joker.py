import random
from abc import ABC, abstractmethod

from question_context import QuestionContext


class Joker(ABC):
    key: str
    label: str

    def __init__(self) -> None:
        self.used = False

    @abstractmethod
    def apply(self, ctx: QuestionContext) -> str:
        """Applique l'effet et retourne un message pour le joueur."""


class FiftyFifty(Joker):
    key, label = "J", "50/50"

    def apply(self, ctx: QuestionContext) -> str:
        wrong = [i for i in range(len(ctx.question.choices))
                 if i != ctx.question.answer and i not in ctx.hidden]
        ctx.hidden.update(random.sample(wrong, min(2, len(wrong))))
        return "Deux mauvaises réponses ont été retirées !"


class Pass(Joker):
    key, label = "P", "Passer"

    def apply(self, ctx: QuestionContext) -> str:
        ctx.passed = True
        return "Question passée (0 point)."