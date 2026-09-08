import logging

import dash_bootstrap_components as dbc
from dash import dcc, html
from sqlalchemy.orm import sessionmaker

from umcu_ai_apps.llm_evaluation.database.helper import load_reference

logger = logging.getLogger(__name__)

# ── Styling ─────────────────────────────────────────────────────

HIGHLIGHT_STYLE = {
    "missing": {
        "label": "Gemiste informatie",
        "color": "#1191FAA6",
    },
    "error": {
        "label": "Fout",
        "color": "#EC6522AF",
    },
    "trivial": {
        "label": "Triviaal",
        "color": "#005A9C80",
    },
    "wording": {
        "label": "Formulering",
        "color": "#d5d5d5",
    },
}


def build_highlighted_children(
    text: str,
    layers: list[tuple[list[dict], str]],
) -> list[str | html.Mark]:
    """Build a list of Dash children with highlighted spans.

    Each layer is a pair of (selections, style). Selections within a layer
    are rendered as ``html.Mark`` elements; plain text fills the gaps.
    Overlapping marks are skipped (first-come, first-served after sorting
    by start position).

    Parameters
    ----------
    text : str
        The full source string to highlight within.
    layers : list[tuple[list[dict], str]]
        Each element is a 2-tuple ``(selections, style)`` where *selections*
        is a list of dicts with ``"start"`` and ``"end"`` integer keys, and
        *style* is a string containing the background color.

    Returns
    -------
    list[str | html.Mark]
        Dash-renderable children: plain strings interspersed with
        ``html.Mark`` components.
    """
    marks = sorted(
        (
            (selection["start"], selection["end"], color)
            for selections, color in layers
            for selection in selections
        ),
        key=lambda mark: mark[0],
    )

    children: list[str | html.Mark] = []
    last_end = 0

    for start, end, color in marks:
        if start < last_end:
            continue

        if last_end < start:
            children.append(text[last_end:start])

        children.append(
            html.Mark(
                text[start:end],
                style={
                    "background": color,
                    "padding": "2px 4px",
                    "borderRadius": "3px",
                },
            )
        )
        last_end = end

    children.append(text[last_end:])
    return children


def rebuild_panel(
    text: str,
    markings: list[dict],
    show_types: set[str],
) -> list[str | html.Mark]:
    """Build highlighted children for a text panel.

    Filters *markings* to the requested types and renders them as
    ``html.Mark`` elements over *text*.

    Parameters
    ----------
    text : str
        The source string to highlight within.
    markings : list[dict]
        The full list of marking entries (each with ``"type"`` and
        ``"sel"`` keys).
    show_types : set[str]
        Which marking types to render (e.g. ``{"missing"}`` or
        ``{"error", "trivial"}``).

    Returns
    -------
    list[str | html.Mark]
        Dash-renderable children for the text panel.
    """
    return build_highlighted_children(
        text,
        [
            (
                [e["sel"] for e in markings if e["type"] == t],
                HIGHLIGHT_STYLE[t]["color"],
            )
            for t in show_types
        ],
    )


def is_duplicate(sel: dict, markings: list[dict]) -> bool:
    """Check whether an identical selection already exists in *markings*.

    Two selections are considered duplicates when they share the same
    ``"start"`` and ``"end"`` offsets, regardless of type.

    Parameters
    ----------
    sel : dict
        A selection dict with ``"start"`` and ``"end"`` integer keys.
    markings : list[dict]
        The current list of annotation entries.

    Returns
    -------
    bool
        ``True`` if *sel* duplicates an existing entry, ``False`` otherwise.
    """
    return any(
        e["sel"]["start"] == sel["start"] and e["sel"]["end"] == sel["end"]
        for e in markings
    )


def build_table(markings: list[dict]) -> html.P | html.Table:
    """Build an HTML table summarising all saved selections.
    Each row shows the entry's type label, selected text, a checkbox for severity,
    a comment field and a delete button.

    Parameters
    ----------
    markings : list[dict]
        The current list of annotation entries.

    Returns
    -------
    html.P | html.Table
        A placeholder paragraph when *markings* is empty, or a fully
        rendered html.Table otherwise.
    """
    if not markings:
        return html.P("Nog geen selecties opgeslagen.", style={"color": "#999"})

    header = {
        "textAlign": "left",
        "padding": "8px",
        "borderBottom": "2px solid #ddd",
    }
    cell = {"padding": "8px", "borderBottom": "1px solid #eee"}
    del_style = {
        "background": "none",
        "border": "none",
        "cursor": "pointer",
        "fontSize": "1.1rem",
        "color": "#bbb",
        "padding": "2px 6px",
        "borderRadius": "4px",
    }

    rows = []
    for entry in markings:
        meta = HIGHLIGHT_STYLE[entry["type"]]
        rows.append(
            html.Tr(
                [
                    html.Td(
                        meta["label"],
                        style={**cell, "width": "16%"},
                    ),
                    html.Td(
                        html.Span(
                            entry["sel"]["text"],
                            style={"background": meta["color"], "width": "80%"},
                        ),
                        style=cell,
                    ),
                    html.Td(
                        dbc.Checkbox(
                            id={"type": "severe-checkbox", "index": entry["id"]},
                            value=entry["is_severe"],
                        ),
                        style={**cell, "width": "8%", "textAlign": "center"},
                    ),
                    html.Td(
                        dcc.Input(
                            id={"type": "comment-input", "index": entry["id"]},
                            type="text",
                            value=entry["comment"],
                            debounce=True,
                            placeholder="Opmerking...",
                            style={"width": "100%"},
                        ),
                        style={**cell, "width": "26%"},
                    ),
                    html.Td(
                        html.Button(
                            "✕",
                            id={"type": "delete-btn", "index": entry["id"]},
                            n_clicks=0,
                            style=del_style,
                            title="Verwijder",
                        ),
                        style={**cell, "textAlign": "center"},
                    ),
                ]
            )
        )

    return html.Table(
        style={
            "width": "100%",
            "borderCollapse": "collapse",
            "marginTop": "1rem",
        },
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th("Type", style=header),
                        html.Th("Selectie", style=header),
                        html.Th("Ernstig", style=header),
                        html.Th("Opmerking", style=header),
                        html.Th("", style={**header, "width": "3rem"}),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
    )


def full_rebuild(
    session_factory: sessionmaker,
    ref_id: int,
) -> tuple[list[str | html.Mark], list[str | html.Mark], html.P | html.Table]:
    """Reload the reference from the database and recompute the full UI.

    This is the single source of truth after any mutation: it queries
    the database for texts and markings, then rebuilds both text panels
    and the table.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    ref_id : int
        The currently selected Reference.id.

    Returns
    -------

    left_children : list[str | html.Mark]
        Updated children for the left (context) text panel.
    right_children : list[str | html.Mark]
        Updated children for the right (LLM review) text panel.
    table : html.P | html.Table
        Updated selection table component.
    """
    ref = load_reference(session_factory, ref_id)
    markings = ref["markings"]
    return (
        rebuild_panel(ref["context"], markings, {"missing"}),
        rebuild_panel(ref["llm"], markings, {"error", "trivial", "wording"}),
        build_table(markings),
    )
