import json
import os
from pathlib import Path
from typing import Literal, cast

from dash import (
    ALL,
    ClientsideFunction,
    Dash,
    Input,
    Output,
    State,
    ctx,
    dcc,
    html,
    no_update,
)
from dotenv import load_dotenv
from flask import logging
from sqlalchemy.orm import sessionmaker
from umcu_ai_utils.database_connection import get_engine

from umcu_ai_apps.llm_evaluation.models import Reference

load_dotenv()
logger = logging.getLogger(__name__)

db_env = cast(Literal["PROD", "ACC", "DEBUG"], os.getenv("DB_ENVIRONMENT"))
SESSIONMAKER = sessionmaker(
    bind=get_engine(db_env=db_env, schema_name=Reference.__table__.schema)
)


# ── App ─────────────────────────────────────────────────────────

app = Dash(
    __name__, assets_folder=Path(__file__).parent / "../src/umcu_ai_apps/llm_evaluation"
)

# ── Dummy data (will be replaced by database queries) ─────────
# Each entry is keyed by enc_id and contains the context and LLM
# source texts that belong to that encounter.
ENCOUNTERS: dict[str, dict] = {
    "ENC-001": {
        "label": "ENC-001 — Consult cardiologie 12-03-2026",
        "context": (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
            "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
            "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
            "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
            "culpa qui officia deserunt mollit anim id est laborum. "
            "Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. "
            "Nullam varius, turpis et commodo pharetra, est eros bibendum elit, "
            "nec luctus magna felis sollicitudin mauris. Integer in mauris eu "
            "nibh euismod gravida. Duis ac tellus et risus vulputate vehicula. "
            "Donec lobortis risus a elit. Etiam tempor. Ut ullamcorper, ligula "
            "ut dictum pharetra, nisi nunc fringilla magna, in commodo elit erat "
            "nec turpis. Ut pharetra augue nec augue."
        ),
        "llm": (
            "Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. "
            "Nullam varius, turpis et commodo pharetra, est eros bibendum elit, "
            "nec luctus magna felis sollicitudin mauris. Integer in mauris eu "
            "nibh euismod gravida. Duis ac tellus et risus vulputate vehicula. "
            "Donec lobortis risus a elit. Etiam tempor. Ut ullamcorper, ligula "
            "ut dictum pharetra, nisi nunc fringilla magna, in commodo elit erat "
            "nec turpis. Ut pharetra augue nec augue. "
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
            "nisi ut aliquip ex ea commodo consequat."
        ),
        "markings": [
            {
                "id": 1,
                "type": "missing",
                "sel": {
                    "text": "Excepteur sint occaecat cupidatat non proident, "
                    "sunt in culpa qui officia deserunt mollit anim id "
                    "est laborum.",
                    "start": 335,
                    "end": 445,
                },
            },
            {
                "id": 2,
                "type": "missing",
                "sel": {
                    "text": "Nullam varius, turpis et commodo pharetra, est "
                    "eros bibendum elit, nec luctus magna felis "
                    "sollicitudin mauris.",
                    "start": 508,
                    "end": 618,
                },
            },
            {
                "id": 3,
                "type": "error",
                "sel": {
                    "text": "Donec lobortis risus a elit. Etiam tempor.",
                    "start": 260,
                    "end": 302,
                },
            },
            {
                "id": 4,
                "type": "trivial",
                "sel": {
                    "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                    "start": 435,
                    "end": 491,
                },
            },
        ],
    },
    "ENC-002": {
        "label": "ENC-002 — Intake neurologie 18-05-2026",
        "context": (
            "Pellentesque habitant morbi tristique senectus et netus et "
            "malesuada fames ac turpis egestas. Vestibulum tortor quam, "
            "feugiat vitae, ultricies eget, tempor sit amet, ante. Donec eu "
            "libero sit amet quam egestas semper. Aenean ultricies mi vitae "
            "est. Mauris placerat eleifend leo. Quisque sit amet est et sapien "
            "ullamcorper pharetra. Vestibulum erat wisi, condimentum sed, "
            "commodo vitae, ornare sit amet, wisi. Aenean fermentum, elit "
            "eget tincidunt condimentum, eros ipsum rutrum orci, sagittis "
            "tempus lacus enim ac dui."
        ),
        "llm": (
            "Aenean fermentum, elit eget tincidunt condimentum, eros ipsum "
            "rutrum orci, sagittis tempus lacus enim ac dui. Donec non enim "
            "in turpis pulvinar facilisis. Ut felis. Praesent dapibus, neque "
            "id cursus faucibus, tortor neque egestas augue, eu vulputate "
            "magna eros eu erat. Aliquam erat volutpat. Nam dui mi, tincidunt "
            "quis, accumsan porttitor, facilisis luctus, metus."
        ),
        "markings": [
            {
                "id": 1,
                "type": "missing",
                "sel": {
                    "text": "Mauris placerat eleifend leo.",
                    "start": 249,
                    "end": 278,
                },
            },
            {
                "id": 2,
                "type": "error",
                "sel": {
                    "text": "Donec non enim in turpis pulvinar facilisis.",
                    "start": 110,
                    "end": 154,
                },
            },
            {
                "id": 3,
                "type": "trivial",
                "sel": {
                    "text": "Aliquam erat volutpat.",
                    "start": 270,
                    "end": 292,
                },
            },
        ],
    },
    "ENC-003": {
        "label": "ENC-003 — Polikliniek orthopedie 02-07-2026",
        "context": (
            "Fusce dapibus, tellus ac cursus commodo, tortor mauris "
            "condimentum nibh, ut fermentum massa justo sit amet risus. "
            "Etiam porta sem malesuada magna mollis euismod. Donec sed odio "
            "dui. Maecenas sed diam eget risus varius blandit sit amet non "
            "magna. Cras mattis consectetur purus sit amet fermentum. "
            "Praesent commodo cursus magna, vel scelerisque nisl consectetur "
            "et. Nullam id dolor id nibh ultricies vehicula ut id elit."
        ),
        "llm": (
            "Praesent commodo cursus magna, vel scelerisque nisl consectetur "
            "et. Nullam id dolor id nibh ultricies vehicula ut id elit. "
            "Maecenas faucibus mollis interdum. Cras justo odio, dapibus ut "
            "facilisis in, egestas eget quam. Vivamus sagittis lacus vel "
            "augue laoreet rutrum faucibus dolor auctor. Morbi leo risus, "
            "porta ac consectetur ac, vestibulum at eros."
        ),
        "markings": [
            {
                "id": 1,
                "type": "missing",
                "sel": {
                    "text": "Etiam porta sem malesuada magna mollis euismod.",
                    "start": 114,
                    "end": 161,
                },
            },
            {
                "id": 2,
                "type": "error",
                "sel": {
                    "text": "Maecenas faucibus mollis interdum.",
                    "start": 123,
                    "end": 157,
                },
            },
        ],
    },
    "ENC-004": {
        "label": "ENC-004 — Spoedopvang 11-08-2026",
        "context": (
            "Nulla vitae elit libero, a pharetra augue. Cum sociis natoque "
            "penatibus et magnis dis parturient montes, nascetur ridiculus "
            "mus. Donec ullamcorper nulla non metus auctor fringilla. "
            "Integer posuere erat a ante venenatis dapibus posuere velit "
            "aliquet. Aenean lacinia bibendum nulla sed consectetur. "
            "Vestibulum id ligula porta felis euismod semper. Cras mattis "
            "consectetur purus sit amet fermentum."
        ),
        "llm": (
            "Vestibulum id ligula porta felis euismod semper. Cras mattis "
            "consectetur purus sit amet fermentum. Aenean lacinia bibendum "
            "nulla sed consectetur. Donec id elit non mi porta gravida at "
            "eget metus. Duis mollis, est non commodo luctus, nisi erat "
            "porttitor ligula, eget lacinia odio sem nec elit."
        ),
        "markings": [],
    },
}

DEFAULT_ENC_ID = "ENC-001"

# ── Styling ─────────────────────────────────────────────────────
HIGHLIGHT_STYLING = {
    "missing": {
        "label": "Gemiste informatie",
        "color": "#1191FAA6",
    },
    "error": {"label": "Fout", "color": "#EC6522AF"},
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


# ── Helpers ─────────────────────────────────────────────────────
def load_markings(enc_id: str) -> list[dict]:
    """Load previously saved markings for an encounter.

    Currently reads from the in-memory ``ENCOUNTERS`` dict.  When a
    database is connected, replace the body of this function with a
    query on *enc_id* and return the result in the same format.

    Parameters
    ----------
    enc_id : str
        The encounter ID whose markings should be loaded.

    Returns
    -------
    list[dict]
        A list of marking entries, each with ``"id"``, ``"type"``, and
        ``"sel"`` keys. Returns an empty list when no markings exist.
    """
    import copy

    return copy.deepcopy(ENCOUNTERS[enc_id].get("markings", []))


def next_id(markings: list[dict]) -> int:
    """Return the next unique integer ID for a new marking entry.

    Parameters
    ----------
    markings : list[dict]
        List of marking entries, each containing an ``"id"`` key with an
        integer value.

    Returns
    -------
    int
        One more than the current maximum ID, or 1 when *markings* is
        empty.
    """
    return max((e["id"] for e in markings), default=0) + 1


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
        key=lambda mark: mark[0],  # sort based on start position
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

    Each row shows the entry's type icon, label, selected text, and a
    delete button.

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

    header = {"textAlign": "left", "padding": "8px", "borderBottom": "2px solid #ddd"}
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
        style={"width": "100%", "borderCollapse": "collapse", "marginTop": "1rem"},
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
    markings: list[dict],
    enc_id: str,
) -> tuple[
    list[dict], list[str | html.Mark], list[str | html.Mark], html.P | html.Table
]:
    """Recompute every dynamic UI element from *markings*.

    This is the single source of truth after any mutation: it rebuilds
    both text panels and the table.

    Parameters
    ----------
    markings : list[dict]
        The current list of annotation entries.
    enc_id : str
        The currently selected encounter ID, used to look up the source
        texts.

    Returns
    -------
    markings : list[dict]
        The (unchanged) markings, returned so it can be written back to
        the store in one tuple-unpack.
    left_children : list[str | html.Mark]
        Updated children for the left (context) text panel.
    right_children : list[str | html.Mark]
        Updated children for the right (LLM review) text panel.
    table : html.P | html.Table
        Updated selection table component.
    """
    enc = ENCOUNTERS[enc_id]
    return (
        markings,
        rebuild_panel(enc["context"], markings, {"missing"}),
        rebuild_panel(enc["llm"], markings, {"error", "trivial"}),
        build_table(markings),
    )


# ── Layout ──────────────────────────────────────────────────────
# Pre-compute the initial state so markings for the default encounter
# are visible immediately without waiting for a callback.
_initial_markings = load_markings(DEFAULT_ENC_ID)
_initial_enc = ENCOUNTERS[DEFAULT_ENC_ID]

app.layout = html.Div(
    style={"maxWidth": "1200px", "margin": "2rem auto", "fontFamily": "sans-serif"},
    children=[
        html.H1("LLM Evaluatie Applicatie"),
        dcc.Store(id="selection-store", data=""),
        dcc.Store(id="markings-store", data=_initial_markings),
        dcc.Store(id="enc-id-store", data=DEFAULT_ENC_ID),
        # ── Encounter selector ────────────────────────────────
        html.Div(
            style={"marginBottom": "1.5rem"},
            children=[
                html.Label(
                    "Selecteer encounter",
                    htmlFor="enc-dropdown",
                    style={
                        "fontWeight": "600",
                        "fontSize": "1.05rem",
                        "marginBottom": "0.4rem",
                        "display": "block",
                    },
                ),
                dcc.Dropdown(
                    id="enc-dropdown",
                    options=[
                        {"label": enc["label"], "value": enc_id}
                        for enc_id, enc in ENCOUNTERS.items()
                    ],
                    value=DEFAULT_ENC_ID,
                    clearable=False,
                    style={"maxWidth": "500px"},
                ),
            ],
        ),
        # ── Two-column text panels ────────────────────────────
        html.Div(
            style={"display": "flex", "gap": "1.5rem", "marginBottom": "1rem"},
            children=[
                html.Div(
                    style={"flex": "1"},
                    children=[
                        html.H3(
                            "Meegestuurde context", style={"marginBottom": "0.5rem"}
                        ),
                        html.Div(
                            id="source-text",
                            children=rebuild_panel(
                                _initial_enc["context"],
                                _initial_markings,
                                {"missing"},
                            ),
                            style=COLUMN_STYLE,
                        ),
                        html.Div(
                            style={
                                "display": "flex",
                                "gap": "0.5rem",
                                "marginTop": "0.8rem",
                            },
                            children=[
                                html.Button(
                                    "Markeer als gemiste informatie",
                                    id="save-btn",
                                    n_clicks=0,
                                    style={
                                        **BTN_BASE,
                                        "background": HIGHLIGHT_STYLING["missing"][
                                            "color"
                                        ],
                                    },
                                ),
                            ],
                        ),
                        html.Div(
                            id="status-missing",
                            style={"marginTop": "0.5rem", "fontSize": "0.9rem"},
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": "1"},
                    children=[
                        html.H3("LLM Resultaat", style={"marginBottom": "0.5rem"}),
                        html.Div(
                            id="source-text-errors",
                            children=rebuild_panel(
                                _initial_enc["llm"],
                                _initial_markings,
                                {"error", "trivial"},
                            ),
                            style=COLUMN_STYLE,
                        ),
                        html.Div(
                            style={
                                "display": "flex",
                                "gap": "0.5rem",
                                "marginTop": "0.8rem",
                                "flexWrap": "wrap",
                            },
                            children=[
                                html.Button(
                                    "Markeer als fout",
                                    id="error-btn",
                                    n_clicks=0,
                                    style={
                                        **BTN_BASE,
                                        "background": HIGHLIGHT_STYLING["error"][
                                            "color"
                                        ],
                                    },
                                ),
                                html.Button(
                                    "Markeer als triviale informatie",
                                    id="trivial-btn",
                                    n_clicks=0,
                                    style={
                                        **BTN_BASE,
                                        "background": HIGHLIGHT_STYLING["trivial"][
                                            "color"
                                        ],
                                    },
                                ),
                            ],
                        ),
                        html.Div(
                            id="status-review",
                            style={"marginTop": "0.5rem", "fontSize": "0.9rem"},
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="status-global", style={"fontSize": "0.9rem", "marginBottom": "0.5rem"}
        ),
        html.Div(
            id="table-container",
            children=[build_table(_initial_markings)],
            style={"marginTop": "0.5rem"},
        ),
    ],
)

app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="capture_selection"),
    Output("selection-store", "data"),
    Input("save-btn", "n_clicks"),
    Input("error-btn", "n_clicks"),
    Input("trivial-btn", "n_clicks"),
    prevent_initial_call=True,
)

SHARED_OUTPUTS = [
    Output("markings-store", "data", allow_duplicate=True),
    Output("source-text", "children", allow_duplicate=True),
    Output("source-text-errors", "children", allow_duplicate=True),
    Output("table-container", "children", allow_duplicate=True),
]


# ── Encounter wisselen ────────────────────────────────────────
@app.callback(
    *SHARED_OUTPUTS,
    Output("enc-id-store", "data"),
    Output("status-missing", "children", allow_duplicate=True),
    Output("status-review", "children", allow_duplicate=True),
    Input("enc-dropdown", "value"),
    prevent_initial_call=True,
)
def handle_encounter_change(enc_id: str) -> tuple:
    """Switch to a different encounter: load its texts and stored markings.

    Parameters
    ----------
    enc_id : str
        The newly selected encounter ID from the dropdown.

    Returns
    -------
    tuple
        Loaded markings, rendered text panels, table, updated enc_id
        store, and cleared status messages.
    """
    markings = load_markings(enc_id)
    return (*full_rebuild(markings, enc_id), enc_id, "", "")


# ── Eén server callback voor opslaan ──────────────────────────
@app.callback(
    *SHARED_OUTPUTS,
    Output("status-missing", "children", allow_duplicate=True),
    Output("status-review", "children", allow_duplicate=True),
    Input("selection-store", "data"),
    State("markings-store", "data"),
    State("enc-id-store", "data"),
    prevent_initial_call=True,
)
def handle_save(raw: str, markings: list[dict], enc_id: str) -> tuple:
    """Process a new selection captured by the client-side callback.

    Validates the payload, checks for duplicates, appends the entry to
    *markings*, and triggers a full UI rebuild.

    Parameters
    ----------
    raw : str
        JSON string produced by the client-side ``capture_selection``
        callback. Contains ``"text"``, ``"start"``, ``"end"``, and
        ``"type"`` keys, or is empty when no text was selected.
    markings : list[dict]
        The current list of annotation entries (from the store).

    Returns
    -------
    tuple
        A 6-element tuple matching the callback outputs: the four shared
        outputs from ``full_rebuild`` plus per-column status messages.
    """
    sel = json.loads(raw)

    if not sel:
        return (
            *([no_update] * 4),
            html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
            html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
        )

    sel_type = sel.pop("type")

    if is_duplicate(sel, markings):
        msg = html.Span("ℹ Al gemarkeerd.", style={"color": "#3b82f6"})
        if sel_type == "missing":
            return *([no_update] * 4), msg, no_update
        else:
            return *([no_update] * 4), no_update, msg

    entry = {"id": next_id(markings), "type": sel_type, "sel": sel}
    markings = markings + [entry]

    # Status alleen tonen in de kolom waar de actie vandaan kwam
    if sel_type == "missing":
        return (*full_rebuild(markings, enc_id), "", no_update)
    return (*full_rebuild(markings, enc_id), no_update, "")


# ── Verwijder via kruisje ─────────────────────────────────────
@app.callback(
    *SHARED_OUTPUTS,
    Input({"type": "delete-btn", "index": ALL}, "n_clicks"),
    State("markings-store", "data"),
    State("enc-id-store", "data"),
    prevent_initial_call=True,
)
def handle_delete(n_clicks_list: list[int], markings: list[dict], enc_id: str) -> tuple:
    """Remove a single entry from *markings* when its delete button is clicked.

    Parameters
    ----------
    n_clicks_list : list[int]
        Click counts for every delete button currently rendered (pattern-
        matching ``ALL``).
    markings : list[dict]
        The current list of annotation entries (from the store).

    Returns
    -------
    tuple
        A 4-element tuple matching the callback outputs: the four shared
        outputs from ``full_rebuild``.
    """
    if not any(n_clicks_list):
        return [no_update] * 4

    triggered = ctx.triggered_id
    if not triggered:
        return [no_update] * 4

    removed = next((e for e in markings if e["id"] == triggered["index"]), None)
    if not removed:
        return [no_update] * 4

    markings = [e for e in markings if e["id"] != triggered["index"]]
    return full_rebuild(markings, enc_id)


if __name__ == "__main__":
    app.run(port=8017, debug=True)
