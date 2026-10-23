#!/usr/bin/env python3
"""Quiz chronométré multijoueur (2 à 4 joueurs en local) - version POO.

Fonctionnalités :
  - QCM par catégorie, questions stockées dans un fichier JSON
  - Compte à rebours par question
  - Jokers : 50/50 et Passer
  - Classement persistant (leaderboard.json)
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LETTERS = "ABCD"


# ----------------------------------------------------------------------
#  Saisie avec temps limité (compte à rebours en direct)
# ----------------------------------------------------------------------
def timed_input(prompt: str, deadline: float) -> str | None:
    """Lit une ligne jusqu'à `deadline` (time.monotonic). Retourne None si le temps est écoulé."""
    if not sys.stdin.isatty():  # pas de terminal (tests / pipe) : pas de timer
        return input(prompt)

    def render(buf: str) -> None:
        left = max(0, int(deadline - time.monotonic() + 0.99))
        sys.stdout.write(f"\r\033[K⏱  {left:2d}s  {prompt}{buf}")
        sys.stdout.flush()

    buf = ""
    if os.name == "nt":
        import msvcrt
        os.system("")  # active les codes ANSI sous Windows 10+
        while time.monotonic() < deadline:
            render(buf)
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in "\r\n":
                    print()
                    return buf
                buf = buf[:-1] if ch == "\b" else buf + ch
            else:
                time.sleep(0.05)
    else:
        import select
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while time.monotonic() < deadline:
                render(buf)
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if ready:
                    ch = sys.stdin.read(1)
                    if ch in "\r\n":
                        print()
                        return buf
                    buf = buf[:-1] if ch in "\x7f\b" else buf + ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    print()
    return None


# ----------------------------------------------------------------------
#  Modèle : Question / banque de questions
# ----------------------------------------------------------------------
@dataclass
class Question:
    text: str
    choices: list[str]
    answer: int  # index de la bonne réponse

    def shuffled(self) -> "Question":
        """Retourne une copie avec les choix mélangés."""
        order = list(range(len(self.choices)))
        random.shuffle(order)
        return Question(
            self.text,
            [self.choices[i] for i in order],
            order.index(self.answer),
        )


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
        while len(picked) < n:  # on recommence un tour de pool si besoin
            picked += random.sample(pool, min(n - len(picked), len(pool)))
        return [q.shuffled() for q in picked]


# ----------------------------------------------------------------------
#  Jokers (polymorphisme : chaque joker implémente apply())
# ----------------------------------------------------------------------
class Joker(ABC):
    key: str
    label: str

    def __init__(self) -> None:
        self.used = False

    @abstractmethod
    def apply(self, ctx: "QuestionContext") -> str:
        """Applique l'effet et retourne un message pour le joueur."""


class FiftyFifty(Joker):
    key, label = "J", "50/50"

    def apply(self, ctx: "QuestionContext") -> str:
        wrong = [i for i in range(len(ctx.question.choices))
                 if i != ctx.question.answer and i not in ctx.hidden]
        ctx.hidden.update(random.sample(wrong, min(2, len(wrong))))
        return "Deux mauvaises réponses ont été retirées !"


class Pass(Joker):
    key, label = "P", "Passer"

    def apply(self, ctx: "QuestionContext") -> str:
        ctx.passed = True
        return "Question passée (0 point)."


@dataclass
class QuestionContext:
    question: Question
    hidden: set[int] = field(default_factory=set)
    passed: bool = False


# ----------------------------------------------------------------------
#  Joueur
# ----------------------------------------------------------------------
class Player:
    def __init__(self, name: str):
        self.name = name
        self.score = 0
        self.jokers: dict[str, Joker] = {j.key: j for j in (FiftyFifty(), Pass())}

    def available_jokers(self) -> list[Joker]:
        return [j for j in self.jokers.values() if not j.used]

    def add_points(self, pts: int) -> None:
        self.score += pts


# ----------------------------------------------------------------------
#  Classement persistant
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
#  Jeu
# ----------------------------------------------------------------------
class QuizGame:
    TIME_PER_QUESTION = 15      # secondes
    QUESTIONS_PER_PLAYER = 5
    BASE_POINTS = 10
    MAX_TIME_BONUS = 10

    def __init__(self, bank: QuestionBank, leaderboard: Leaderboard):
        self.bank = bank
        self.leaderboard = leaderboard
        self.players: list[Player] = []

    # ---- configuration ------------------------------------------------
    def setup(self) -> str:
        print("=" * 50)
        print("   🎯  QUIZ CHRONOMÉTRÉ MULTIJOUEUR")
        print("=" * 50)
        while True:
            n = input("Nombre de joueurs (2 à 4) : ").strip()
            if n.isdigit() and 2 <= int(n) <= 4:
                break
            print("→ Entrez un nombre entre 2 et 4.")
        for i in range(int(n)):
            while True:
                name = input(f"Nom du joueur {i + 1} : ").strip() or f"Joueur{i + 1}"
                if name.lower() in (p.name.lower() for p in self.players):
                    print("→ Ce nom est déjà pris, choisissez-en un autre.")
                    continue
                break
            self.players.append(Player(name))

        print("\nCatégories :")
        cats = self.bank.categories
        for i, c in enumerate(cats, 1):
            print(f"  {i}. {c}")
        while True:
            c = input("Choisissez une catégorie : ").strip()
            if c.isdigit() and 1 <= int(c) <= len(cats):
                return cats[int(c) - 1]
            print("→ Choix invalide.")

    # ---- déroulement --------------------------------------------------
    def run(self) -> None:
        category = self.setup()
        total_q = self.QUESTIONS_PER_PLAYER * len(self.players)
        questions = self.bank.draw(category, total_q)

        print(f"\nCatégorie : {category} | {self.TIME_PER_QUESTION}s par question")
        print("Réponses : A/B/C/D | J = 50/50 | P = Passer (1 fois chacun)\n")

        for i, q in enumerate(questions):
            player = self.players[i % len(self.players)]
            print("-" * 50)
            print(f"Question {i + 1}/{len(questions)}  →  🎮 {player.name}  (score : {player.score})")
            self.ask(player, q)

        self.finish()

    def ask(self, player: Player, question: Question) -> None:
        ctx = QuestionContext(question)
        start = time.monotonic()
        deadline = start + self.TIME_PER_QUESTION

        while True:
            self._display(ctx, player)
            raw = timed_input("> ", deadline)
            if raw is None:
                print("⌛ Temps écoulé ! 0 point.")
                return
            choice = raw.strip().upper()

            joker = player.jokers.get(choice)
            if joker is not None:
                if joker.used:
                    print("→ Joker déjà utilisé.")
                    continue
                joker.used = True
                print("✨", joker.apply(ctx))
                if ctx.passed:
                    return
                continue

            if choice and choice in LETTERS[:len(question.choices)]:
                idx = LETTERS.index(choice)
                if idx in ctx.hidden:
                    print("→ Cette réponse a été retirée.")
                    continue
                remaining = max(0.0, deadline - time.monotonic())
                if idx == question.answer:
                    bonus = int(self.MAX_TIME_BONUS * remaining / self.TIME_PER_QUESTION)
                    pts = self.BASE_POINTS + bonus
                    player.add_points(pts)
                    print(f"✅ Bonne réponse ! +{pts} points (bonus temps : {bonus})")
                else:
                    good = question.choices[question.answer]
                    print(f"❌ Faux. La bonne réponse était : {LETTERS[question.answer]}. {good}")
                return
            print("→ Entrée invalide.")

    @staticmethod
    def _display(ctx: QuestionContext, player: Player) -> None:
        print(f"\n❓ {ctx.question.text}")
        for i, c in enumerate(ctx.question.choices):
            shown = "---" if i in ctx.hidden else c
            print(f"   {LETTERS[i]}. {shown}")
        jokers = ", ".join(f"{j.key}={j.label}" for j in player.available_jokers())
        print(f"   Jokers : {jokers or 'aucun'}")

    # ---- fin de partie ------------------------------------------------
    def finish(self) -> None:
        print("\n" + "=" * 50)
        print("   🏁  RÉSULTATS DE LA PARTIE")
        print("=" * 50)
        ranked = sorted(self.players, key=lambda p: p.score, reverse=True)
        medals = ["🥇", "🥈", "🥉", "  "]
        for i, p in enumerate(ranked):
            print(f" {medals[i]} {p.name:<15} {p.score} pts")
        self.leaderboard.record(self.players)
        self.leaderboard.show()


def main() -> None:
    bank = QuestionBank(BASE_DIR / "questions.json")
    board = Leaderboard(BASE_DIR / "leaderboard.json")
    while True:
        QuizGame(bank, board).run()
        if input("\nRejouer ? (o/n) : ").strip().lower() != "o":
            print("À bientôt ! 👋")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPartie interrompue.")