from dash import dcc, html

from umcu_ai_apps.llm_evaluation.helper import (
    BTN_BASE,
    COLUMN_STYLE,
    HIGHLIGHT_STYLING,
    build_table,
)


def create_layout(
    dropdown_options: list[dict],
) -> html.Div:
    """Build the app layout.

    Texts and markings are loaded by the reference-change callback
    which fires on page load (prevent_initial_call=False).

    Parameters
    ----------
    dropdown_options : list[dict]
        Pre-loaded options for the reference dropdown.
    default_ref_id : int | None
        Initial dropdown value, or ``None`` when no references exist.
    """
    return html.Div(
        style={
            "maxWidth": "1200px",
            "margin": "2rem auto",
            "fontFamily": "sans-serif",
        },
        children=[
            html.H1("LLM Evaluatie Applicatie"),
            dcc.Store(id="selection-store", data=""),
            dcc.Store(id="markings-store", data=[]),
            # ── Reference selector ────────────────────────────
            html.Div(
                style={"marginBottom": "1.5rem"},
                children=[
                    html.Label(
                        "Selecteer referentie",
                        htmlFor="ref-dropdown",
                        style={
                            "fontWeight": "600",
                            "fontSize": "1.05rem",
                            "marginBottom": "0.4rem",
                            "display": "block",
                        },
                    ),
                    dcc.Dropdown(
                        id="ref-dropdown",
                        options=dropdown_options,
                        value=dropdown_options[0]["value"]
                        if dropdown_options
                        else None,
                        clearable=False,
                        style={"maxWidth": "500px"},
                    ),
                ],
            ),
            # ── Two-column text panels ────────────────────────
            html.Div(
                style={
                    "display": "flex",
                    "gap": "1.5rem",
                    "marginBottom": "1rem",
                },
                children=[
                    html.Div(
                        style={"flex": "1"},
                        children=[
                            html.H3(
                                "Meegestuurde context",
                                style={"marginBottom": "0.5rem"},
                            ),
                            html.Div(
                                id="source-text",
                                children=[],
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
                                id="status-left",
                                style={
                                    "marginTop": "0.5rem",
                                    "fontSize": "0.9rem",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        style={"flex": "1"},
                        children=[
                            html.H3(
                                "LLM Resultaat",
                                style={"marginBottom": "0.5rem"},
                            ),
                            html.Div(
                                id="source-text-errors",
                                children=[],
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
                                id="status-right",
                                style={
                                    "marginTop": "0.5rem",
                                    "fontSize": "0.9rem",
                                },
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="status-global",
                style={"fontSize": "0.9rem", "marginBottom": "0.5rem"},
            ),
            html.Div(
                id="table-container",
                children=[build_table([])],
                style={"marginTop": "0.5rem"},
            ),
        ],
    )
