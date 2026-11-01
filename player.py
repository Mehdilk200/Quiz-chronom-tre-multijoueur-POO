from joker import FiftyFifty, Joker, Pass


class Player:
    def __init__(self, name: str):
        self.name = name
        self.score = 0
        self.jokers: dict[str, Joker] = {j.key: j for j in (FiftyFifty(), Pass())}

    def available_jokers(self) -> list[Joker]:
        return [j for j in self.jokers.values() if not j.used]

    def add_points(self, pts: int) -> None:
        self.score += pts