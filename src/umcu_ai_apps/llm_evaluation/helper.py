import json
import logging
from datetime import datetime

import flask
from dash import html
from flask import Request
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from umcu_ai_apps.llm_evaluation.models import (
    Marking,
    Reference,
    User,
)

logger = logging.getLogger(__name__)

# ── Styling ─────────────────────────────────────────────────────

HIGHLIGHT_STYLING = {
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
        "color": "#d5d5d5",
    },
}

COLUMN_STYLE = {
    "flex": "1",
    "height": "400px",
    "overflowY": "auto",
    "padding": "1.2rem",
    "background": "#fafafa",
    "border": "1px solid #ddd",
    "borderRadius": "8px",
    "fontSize": "1.05rem",
    "lineHeight": "1.8",
    "userSelect": "text",
    "cursor": "text",
}

BTN_BASE = {
    "border": "none",
    "padding": "0.5rem 1.2rem",
    "borderRadius": "8px",
    "fontSize": "0.95rem",
    "cursor": "pointer",
}


# ── Database helpers ────────────────────────────────────────────

_USER_ID: int | None = None


def get_user_email(req: Request) -> str:
    """Get the user email from RStudio credentials.

    Parameters
    ----------
    req : Request
        The request object.

    Returns
    -------
    str
        The user's email.
    """
    credential_header = req.headers.get("RStudio-Connect-Credentials")
    if not credential_header:
        logger.warning("No credentials found in request headers")
        return "No user"

    credential_header = json.loads(credential_header)
    user = credential_header.get("user").lower()
    return user


def _get_user_id(session_factory: sessionmaker) -> int:
    """Return the DB id for the current user, resolving once and caching.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    """
    global _USER_ID
    if _USER_ID is not None:
        return _USER_ID
    email = get_user_email(flask.request)
    with session_factory() as session:
        user = session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user is None:
            user = User(email=email)
            session.add(user)
            session.commit()
        _USER_ID = user.id
    return _USER_ID


def load_dropdown_options(session_factory: sessionmaker) -> list[dict]:
    """Query reference labels for the reference dropdown.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    """
    with session_factory() as session:
        refs = session.execute(select(Reference)).scalars().all()
        return [
            {
                "label": (f"{r.reference_id} — {r.reference_description or ''}").strip(
                    " —"
                ),
                "value": r.id,
            }
            for r in refs
            if r.evaluation_item_relation is not None and r.context_relation is not None
        ]


def load_reference(session_factory: sessionmaker, ref_id: int) -> dict:
    """Load full reference data from the database.

    Returns context text, LLM response, internal IDs, and the current
    user's markings — everything the UI needs in one query.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    ref_id : int
        The Reference.id to load.

    Returns
    -------
    dict
        Keys: ``"context"``, ``"llm"``, ``"evaluation_item_id"``,
        ``"context_id"``, ``"markings"``.
    """
    with session_factory() as session:
        ref = session.get(Reference, ref_id)
        if ref is None:
            return {
                "context": "",
                "llm": "",
                "evaluation_item_id": None,
                "context_id": None,
                "markings": [],
            }

        eval_item = ref.evaluation_item_relation
        context = ref.context_relation

        db_markings = (
            session.execute(
                select(Marking).where(
                    Marking.evaluation_item_id == eval_item.id,
                    Marking.user_id == _get_user_id(session_factory),
                )
            )
            .scalars()
            .all()
        )

        return {
            "context": context.context_text,
            "llm": eval_item.llm_response,
            "evaluation_item_id": eval_item.id,
            "context_id": context.id,
            "markings": [
                {
                    "id": m.id,
                    "type": m.marking_type,
                    "sel": {
                        "text": m.marking_text,
                        "start": m.marking_start,
                        "end": m.marking_end,
                    },
                }
                for m in db_markings
            ],
        }


def save_marking_to_db(
    session_factory: sessionmaker,
    ref_id: int,
    marking_type: str,
    sel: dict,
) -> None:
    """Insert a new marking into the database.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    ref_id : int
        The Reference.id this marking belongs to.
    marking_type : str
        One of ``"missing"``, ``"error"``, ``"trivial"``.
    sel : dict
        Selection dict with ``"text"``, ``"start"``, ``"end"`` keys.
    """
    with session_factory() as session:
        ref = session.get(Reference, ref_id)
        marking = Marking(
            user_id=_get_user_id(session_factory),
            evaluation_item_id=ref.evaluation_item_relation.id,
            context_id=ref.context_relation.id,
            marking_type=marking_type,
            marking_text=sel["text"],
            marking_start=sel["start"],
            marking_end=sel["end"],
            timestamp=datetime.now(),
        )
        session.add(marking)
        session.commit()


def delete_marking_from_db(
    session_factory: sessionmaker,
    marking_id: int,
) -> None:
    """Delete a marking from the database by its primary key.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory used to open a database session.
    marking_id : int
        The Marking.id to remove.
    """
    with session_factory() as session:
        marking = session.get(Marking, marking_id)
        if marking is not None:
            session.delete(marking)
            session.commit()


# ── UI helpers ──────────────────────────────────────────────────


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
                HIGHLIGHT_STYLING[t]["color"],
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

    Each row shows the entry's type label, selected text, and a delete
    button.

    Parameters
    ----------
    markings : list[dict]
        The current list of annotation entries.

    Returns
    -------
    html.P | html.Table
        A placeholder paragraph when *markings* is empty, or a fully
        rendered ``html.Table`` otherwise.
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
        meta = HIGHLIGHT_STYLING[entry["type"]]
        rows.append(
            html.Tr(
                [
                    html.Td(
                        meta["label"],
                        style={**cell, "width": "20%"},
                    ),
                    html.Td(
                        html.Span(
                            entry["sel"]["text"],
                            style={"background": meta["color"], "width": "80%"},
                        ),
                        style=cell,
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
) -> tuple[
    list[dict], list[str | html.Mark], list[str | html.Mark], html.P | html.Table
]:
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
    markings : list[dict]
        The markings as loaded from the database.
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
        markings,
        rebuild_panel(ref["context"], markings, {"missing"}),
        rebuild_panel(ref["llm"], markings, {"error", "trivial"}),
        build_table(markings),
    )
