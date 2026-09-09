from dataclasses import dataclass
from enum import Enum


class HighlightStyle(Enum):
    """Enumeration of possible highlight styles."""

    label: str
    color: str

    MISSING = ("missing", "Gemiste informatie", "#1191FAA6")
    ERROR = ("error", "Fout", "#EC6522AF")
    TRIVIAL = ("trivial", "Triviaal", "#005A9C80")
    WORDING = ("wording", "Formulering", "#d5d5d5")

    def __new__(cls, value: str, label: str, color: str):
        """Create a new instance of the HighlightStyle enum."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        obj.color = color
        return obj


@dataclass
class Selection:
    """Represents a text selection that was highlighted by the user."""

    text: str
    start: int
    end: int
    type: str


@dataclass
class MarkingData:
    """Represents a marking made by the user."""

    id: int
    sel: Selection
    is_severe: bool
    comment: str


@dataclass
class ReferenceData:
    """Represents a reference along with its associated markings."""

    context: str
    llm: str
    evaluation_item_id: int
    markings: list[MarkingData]
