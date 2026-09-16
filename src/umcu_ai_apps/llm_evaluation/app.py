"""This module contains the Dash app for the LLM evaluation tool.
The app allows users to view LLM responses, mark issues in both the LLM responses and
the reference text, and provide usability feedback. The app is built using Dash and
Bootstrap, and it interacts with a database to store and retrieve markings and
usability scores.
In order to get data into the database that the app can use, run the
`run/prep_llm_evaluation.py` module first.
"""

import json
import logging
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

from umcu_ai_apps.config import configure_logging
from umcu_ai_apps.llm_evaluation.dash.dataclasses import Selection
from umcu_ai_apps.llm_evaluation.dash.helper import (
    full_rebuild,
    is_duplicate,
    load_reference,
)
from umcu_ai_apps.llm_evaluation.dash.layout import create_layout
from umcu_ai_apps.llm_evaluation.database.helper import (
    delete_marking_from_db,
    get_user_id,
    load_dropdown_options,
    load_usability_score,
    save_marking_to_db,
    save_usability_assessment,
    update_marking_comment,
    update_marking_severity,
)
from umcu_ai_apps.llm_evaluation.database.models import (
    Reference,
)

logger = logging.getLogger(__name__)
configure_logging()

load_dotenv()
db_env = cast(Literal["PROD", "ACC", "DEBUG"], os.getenv("DB_ENVIRONMENT"))
SESSIONMAKER = sessionmaker(
    bind=get_engine(db_env=db_env, schema_name=Reference.__table__.schema)
)
app = Dash(
    __name__,
    assets_folder=str(Path(__file__).parent / "dash"),
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

app.layout = create_layout()

app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="capture_selection"),
    Output("selection-store", "data"),
    Input("missing-btn", "n_clicks"),
    Input("error-btn", "n_clicks"),
    Input("trivial-btn", "n_clicks"),
    Input("wording-btn", "n_clicks"),
    prevent_initial_call=True,
)


# Callback that fills the ref_dropdown after the app is loaded
@app.callback(
    Output("ref-dropdown", "options"),
    Output("ref-dropdown", "value"),
    Output("current_user", "data"),
)
def page_load():
    """Callback to fill the reference dropdown and set the current user on page load."""
    current_user = get_user_id(SESSIONMAKER)
    options = load_dropdown_options(SESSIONMAKER, current_user)
    value = options[0]["value"] if options else None
    return options, value, current_user


@app.callback(
    Output("context-text", "children"),
    Output("llm-text", "children"),
    Output("table-container", "children"),
    Output("status-left", "children"),
    Output("status-right", "children"),
    Output("usability-score", "value"),
    Input("selection-store", "data"),
    Input("ref-dropdown", "value"),
    Input({"type": "delete-btn", "index": ALL}, "n_clicks"),
    State("current_user", "data"),
)
def handle_save(
    json_selection: str, reference_id: int, delete_clicks: list[int], current_user: int
) -> tuple:
    """Process a new reference selection, a new marking, or a delete button click.

    This callback is triggered when the user selects a new reference from the dropdown,
    when the user saves a new marking, or when the user clicks a delete button for an
    existing marking. It updates the context text, LLM response text, and table of
    markings accordingly, and returns status messages for the left and right columns.

    Parameters
    ----------
    json_selection : str
        JSON string produced by the client-side ``capture_selection``
        callback. Contains ``"text"``, ``"start"``, ``"end"``, and
        ``"type"`` keys, or is empty when no text was selected.
    reference_id : int
        The currently selected Reference.id (read from the dropdown).
    delete_clicks : list[int]
        List of click counts for every delete button currently rendered.
        Used to determine if a delete button was clicked and which one.

    Returns
    -------
    tuple
        A 6-element tuple containing the following:
        - The context text for the currently selected reference.
        - The LLM response text for the currently selected reference.
        - The table of markings for the currently selected reference.
        - A status message for the left column (context text).
        - A status message for the right column (LLM response text).
        - The current user's usability score for the selected reference.
    """
    triggered = ctx.triggered_id

    # Initial load or new reference selected
    if not triggered or triggered == "ref-dropdown":
        return (
            *full_rebuild(SESSIONMAKER, reference_id, current_user),
            "",
            "",
            load_usability_score(SESSIONMAKER, reference_id, current_user),
        )
    # Handle a new selection being saved
    elif triggered == "selection-store":
        if not json_selection:
            return (
                *([no_update] * 3),
                html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
                html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
                no_update,
            )

        selection_data = json.loads(json_selection)

        if not selection_data:
            return (
                *([no_update] * 3),
                html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
                html.Span("⚠ Selecteer eerst tekst.", style={"color": "orange"}),
                no_update,
            )
        selection_data = Selection(**selection_data)

        markings = load_reference(SESSIONMAKER, reference_id, current_user).markings
        if is_duplicate(selection_data, markings):
            msg = html.Span("ℹ Al gemarkeerd.", style={"color": "#3b82f6"})
            if selection_data.type == "missing":
                return *([no_update] * 3), msg, no_update, no_update
            else:
                return *([no_update] * 3), no_update, msg, no_update

        logger.info(f"Saving new marking with type: {selection_data.type}")
        save_marking_to_db(SESSIONMAKER, reference_id, current_user, selection_data)

        if selection_data.type == "missing":
            return (
                *full_rebuild(SESSIONMAKER, reference_id, current_user),
                "",
                no_update,
                no_update,
            )
        return (
            *full_rebuild(SESSIONMAKER, reference_id, current_user),
            no_update,
            "",
            no_update,
        )
    # Handle a delete button being clicked
    else:
        if not any(delete_clicks):
            return (no_update, no_update, no_update, no_update, no_update, no_update)

        delete_marking_from_db(SESSIONMAKER, triggered["index"])
        logger.info(f"Deleted marking {triggered['index']}")
        return (
            *full_rebuild(SESSIONMAKER, reference_id, current_user),
            no_update,
            no_update,
            no_update,
        )


@app.callback(
    Input({"type": "severe-checkbox", "index": ALL}, "value"),
)
def handle_severity_change(values: list[bool]) -> None:
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
        return

    is_severe = bool(ctx.triggered[0]["value"])
    update_marking_severity(SESSIONMAKER, triggered["index"], is_severe)
    logger.info(f"Saved severity for marking {triggered['index']}: {is_severe}")


@app.callback(
    Input({"type": "comment-input", "index": ALL}, "value"),
)
def handle_comment_change(values: list[str]) -> None:
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
        return

    comment = ctx.triggered[0]["value"] or ""
    update_marking_comment(SESSIONMAKER, triggered["index"], comment)
    logger.info(f"Saved comment for marking {triggered['index']}: {comment}")


@app.callback(
    Input("usability-score", "value"),
    State("ref-dropdown", "value"),
    State("current_user", "data"),
)
def handle_usability_change(score: int | None, ref_id: int, current_user: int) -> None:
    """Persist the current user's usability score as soon as it changes.

    Parameters
    ----------
    score : int | None
        The selected usability score, from 1 to 5.
    ref_id : int
        The currently selected Reference.id (read from the dropdown).
    """
    if not score:
        return

    stored_score = load_usability_score(SESSIONMAKER, ref_id, current_user)
    if score == stored_score:
        return

    reference_data = load_reference(SESSIONMAKER, ref_id, current_user)
    save_usability_assessment(
        SESSIONMAKER, reference_data.evaluation_item_id, score, current_user
    )
    logger.info(f"Saved usability score {score}")


def main() -> None:
    """Run the Dash app."""
    app.run(port=8017, debug=True)


if __name__ == "__main__":
    main()
