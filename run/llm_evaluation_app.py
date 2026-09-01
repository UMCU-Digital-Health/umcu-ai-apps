"""This module contains the Dash app for the LLM evaluation tool.
The app allows users to view LLM responses, mark issues in both the LLM responses and
the reference text, and provide usability feedback. The app is built using Dash and
Bootstrap, and it interacts with a database to store and retrieve markings and
usability scores.
In order to get data into the database that the app can use, run the
`run/prep_llm_evaluation.py` module first.
"""

import json
import os
from pathlib import Path
from typing import Literal, cast

import dash_bootstrap_components as dbc
from dash import (
    ALL,
    ClientsideFunction,
    Dash,
    Input,
    Output,
    State,
    ctx,
    html,
    no_update,
)
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from umcu_ai_utils.database_connection import get_engine

from umcu_ai_apps.llm_evaluation.helper import (
    delete_marking_from_db,
    full_rebuild,
    is_duplicate,
    load_dropdown_options,
    load_reference,
    load_usability_score,
    save_marking_to_db,
    save_usability_assessment,
    update_marking_comment,
    update_marking_severity,
)
from umcu_ai_apps.llm_evaluation.layout import create_layout
from umcu_ai_apps.llm_evaluation.models import (
    Reference,
)

load_dotenv()
db_env = cast(Literal["PROD", "ACC", "DEBUG"], os.getenv("DB_ENVIRONMENT"))
SESSIONMAKER = sessionmaker(
    bind=get_engine(db_env=db_env, schema_name=Reference.__table__.schema)
)
app = Dash(
    __name__,
    assets_folder=Path(__file__).parent / "../src/umcu_ai_apps/llm_evaluation",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
dropdown_options = load_dropdown_options(SESSIONMAKER)

app.layout = create_layout(dropdown_options)

app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="capture_selection"),
    Output("selection-store", "data"),
    Input("save-btn", "n_clicks"),
    Input("error-btn", "n_clicks"),
    Input("trivial-btn", "n_clicks"),
    Input("wording-btn", "n_clicks"),
    prevent_initial_call=True,
)


@app.callback(
    Output("context-text", "children"),
    Output("llm-text", "children"),
    Output("table-container", "children"),
    Output("status-left", "children"),
    Output("status-right", "children"),
    Output("usability-score", "value"),
    Input("ref-dropdown", "value"),
    prevent_initial_call=False,
)
def handle_reference_change(ref_id: int) -> tuple:
    """Switch to a different reference: load its texts and stored markings.

    Also fires on page load (prevent_initial_call=False) to populate the
    initial state from the database.

    Parameters
    ----------
    ref_id : int
        The newly selected Reference.id from the dropdown.

    Returns
    -------
    tuple
        Rendered text panels, table, cleared status messages, and the
        current user's usability score for this reference.
    """
    return (
        *full_rebuild(SESSIONMAKER, ref_id),
        "",
        "",
        load_usability_score(SESSIONMAKER, ref_id),
    )


@app.callback(
    Output("context-text", "children", allow_duplicate=True),
    Output("llm-text", "children", allow_duplicate=True),
    Output("table-container", "children", allow_duplicate=True),
    Output("status-left", "children", allow_duplicate=True),
    Output("status-right", "children", allow_duplicate=True),
    Input("selection-store", "data"),
    State("ref-dropdown", "value"),
    prevent_initial_call=True,
)
def handle_save(raw: str, ref_id: int) -> tuple:
    """Process a new selection captured by the client-side callback.

    Validates the payload, checks for duplicates, saves the marking to
    the database, and reloads from the database for a full UI rebuild.

    Parameters
    ----------
    raw : str
        JSON string produced by the client-side ``capture_selection``
        callback. Contains ``"text"``, ``"start"``, ``"end"``, and
        ``"type"`` keys, or is empty when no text was selected.
    ref_id : int
        The currently selected Reference.id (read from the dropdown).

    Returns
    -------
    tuple
        A 5-element tuple: the three outputs from ``full_rebuild``
        plus per-column status messages.
    """
    if not raw:
        return (
            *([no_update] * 3),
            html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
            html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
        )

    sel = json.loads(raw)

    if not sel:
        return (
            *([no_update] * 3),
            html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
            html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
        )

    sel_type = sel["type"]

    markings = load_reference(SESSIONMAKER, ref_id)["markings"]
    if is_duplicate(sel, markings):
        msg = html.Span("ℹ Al gemarkeerd.", style={"color": "#3b82f6"})
        if sel_type == "missing":
            return *([no_update] * 3), msg, no_update
        else:
            return *([no_update] * 3), no_update, msg

    save_marking_to_db(SESSIONMAKER, ref_id, sel)

    if sel_type == "missing":
        return (*full_rebuild(SESSIONMAKER, ref_id), "", no_update)
    return (*full_rebuild(SESSIONMAKER, ref_id), no_update, "")


@app.callback(
    Output("context-text", "children", allow_duplicate=True),
    Output("llm-text", "children", allow_duplicate=True),
    Output("table-container", "children", allow_duplicate=True),
    Input({"type": "delete-btn", "index": ALL}, "n_clicks"),
    State("ref-dropdown", "value"),
    prevent_initial_call=True,
)
def handle_delete(n_clicks_list: list[int], ref_id: int) -> tuple:
    """Remove a single marking when its delete button is clicked.

    Parameters
    ----------
    n_clicks_list : list[int]
        Click counts for every delete button currently rendered.
    ref_id : int
        The currently selected Reference.id (read from the dropdown).

    Returns
    -------
    tuple
        The three outputs from ``full_rebuild``.
    """
    if not any(n_clicks_list):
        return [no_update] * 3

    triggered = ctx.triggered_id
    if not triggered:
        return [no_update] * 3

    delete_marking_from_db(SESSIONMAKER, triggered["index"])

    return full_rebuild(SESSIONMAKER, ref_id)


@app.callback(
    Input({"type": "severe-checkbox", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def handle_severity_change(values: list[bool]) -> str:
    """Persist a marking's "severe" flag when its checkbox is toggled.
    There is no return value and Output, because the checkbox is already in the correct
     state in the UI and only the database needs to be updated.

    Parameters
    ----------
    values : list[bool]
        Checked state for every severity checkbox currently rendered.
    """
    triggered = ctx.triggered_id
    if not triggered:
        return no_update

    is_severe = bool(ctx.triggered[0]["value"])
    update_marking_severity(SESSIONMAKER, triggered["index"], is_severe)


@app.callback(
    Input({"type": "comment-input", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def handle_comment_change(values: list[str]):
    """Persist a marking's comment when its input loses focus.
    There is no return value and Output, because the checkbox is already in the correct
     state in the UI and only the database needs to be updated.

    Parameters
    ----------
    values : list[str]
        Current text for every comment input currently rendered.
    """
    triggered = ctx.triggered_id
    if not triggered:
        return no_update

    comment = ctx.triggered[0]["value"] or ""
    update_marking_comment(SESSIONMAKER, triggered["index"], comment)


@app.callback(
    Input("usability-score", "value"),
    State("ref-dropdown", "value"),
    prevent_initial_call=True,
)
def handle_usability_change(score: int | None, ref_id: int):
    """Persist the current user's usability score as soon as it changes.

    Parameters
    ----------
    score : int | None
        The selected usability score, from 1 to 5.
    ref_id : int
        The currently selected Reference.id (read from the dropdown).
    """
    if score is None:
        return
    ref = load_reference(SESSIONMAKER, ref_id)
    save_usability_assessment(SESSIONMAKER, ref["evaluation_item_id"], score)


if __name__ == "__main__":
    app.run(port=8017, debug=True)
