from dataclasses import dataclass
from enum import Enum


class HighlightStyle(Enum):
    """
    Enumeration of possible highlight styles.
    Also contains the label and color associated with each highlight style.
    """

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
    """Represents a text selection that was highlighted by the user.

    Attributes
    ----------
    text : str
        The selected text.
    start : int
        The start position of the selection in the text.
    end : int
        The end position of the selection in the text.
    type : str
        The type of the selection, e.g., missing, error, trivial, or wording.
    """

    text: str
    start: int
    end: int
    type: str


@dataclass
class MarkingData:
    """Represents a marking made by the user.

    Attributes
    ----------
    id : int
        The unique identifier of the marking.
    sel : Selection
        The text selection associated with the marking.
    is_severe : bool
        Indicates if the marking is severe.
    comment : str
        Optional comment associated with the marking.

    """

    id: int
    sel: Selection
    is_severe: bool
    comment: str


@dataclass
class ReferenceData:
    """Represents a reference along with its associated markings.

    Attributes
    ----------
    context : str
        The context text of the reference.
    llm : str
        The LLM-generated text of the reference.
    evaluation_item_id : int
        The ID of the associated evaluation item.
    markings : list[MarkingData]
        The list of markings associated with the reference.
    """

    context: str
    llm: str
    evaluation_item_id: int
    markings: list[MarkingData]
