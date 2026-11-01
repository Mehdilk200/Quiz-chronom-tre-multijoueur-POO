from dataclasses import dataclass, field

from question import Question


@dataclass
class QuestionContext:
    question: Question
    hidden: set[int] = field(default_factory=set)
    passed: bool = False