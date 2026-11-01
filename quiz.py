#!/usr/bin/env python3
"""Point d'entrée console et façade publique du quiz."""

from leaderboard import Leaderboard
from joker import FiftyFifty, Joker, Pass
from player import Player
from question import Question
from question_bank import QuestionBank
from question_context import QuestionContext
from quiz_game import QuizGame
from settings import BASE_DIR, LETTERS
from timed_input import timed_input


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