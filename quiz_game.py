import time

from leaderboard import Leaderboard
from player import Player
from question import Question
from question_bank import QuestionBank
from question_context import QuestionContext
from settings import LETTERS
from timed_input import timed_input


class QuizGame:
    TIME_PER_QUESTION = 15
    QUESTIONS_PER_PLAYER = 5
    BASE_POINTS = 10
    MAX_TIME_BONUS = 10

    def __init__(self, bank: QuestionBank, leaderboard: Leaderboard):
        self.bank = bank
        self.leaderboard = leaderboard
        self.players: list[Player] = []

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

    def run(self) -> None:
        category = self.setup()
        total_q = self.QUESTIONS_PER_PLAYER * len(self.players)
        questions = self.bank.draw(category, total_q)

        print(f"\nCatégorie : {category} | {self.TIME_PER_QUESTION}s par question")
        print("Réponses : A/B/C/D | J = 50/50 | P = Passer (1 fois chacun)\n")

        for i, question in enumerate(questions):
            player = self.players[i % len(self.players)]
            print("-" * 50)
            print(f"Question {i + 1}/{len(questions)}  →  🎮 {player.name}  (score : {player.score})")
            self.ask(player, question)

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
        for i, choice in enumerate(ctx.question.choices):
            shown = "---" if i in ctx.hidden else choice
            print(f"   {LETTERS[i]}. {shown}")
        jokers = ", ".join(f"{j.key}={j.label}" for j in player.available_jokers())
        print(f"   Jokers : {jokers or 'aucun'}")

    def finish(self) -> None:
        print("\n" + "=" * 50)
        print("   🏁  RÉSULTATS DE LA PARTIE")
        print("=" * 50)
        ranked = sorted(self.players, key=lambda p: p.score, reverse=True)
        medals = ["🥇", "🥈", "🥉", "  "]
        for i, player in enumerate(ranked):
            print(f" {medals[i]} {player.name:<15} {player.score} pts")
        self.leaderboard.record(self.players)
        self.leaderboard.show()