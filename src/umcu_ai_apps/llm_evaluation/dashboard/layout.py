import dash_bootstrap_components as dbc
from dash import dcc, html
from umcu_ai_utils.dash.layout import get_navbar

from umcu_ai_apps.llm_evaluation.dashboard.dataclasses import HighlightStyle
from umcu_ai_apps.llm_evaluation.dashboard.helper import (
    build_table,
)


def create_layout() -> html.Div:
    """Build the app layout.

    Texts and markings are loaded by the reference-change callback
    which fires on page load (prevent_initial_call=False).

    Returns
    -------
    html.Div
        The complete application layout.
    """
    return html.Div(
        children=[
            # Full-width navbar without margins/padding
            get_navbar(
                "LLM Evaluatie Applicatie",
                view_user=False,
            ),
            # Page content with horizontal margins
            html.Div(
                style={
                    "paddingLeft": "2rem",
                    "paddingRight": "2rem",
                    "paddingTop": "1.5rem",
                },
                children=[
                    dcc.Store(
                        id="selection-store",
                        data="",
                    ),
                    dcc.Store(
                        id="current_user",
                        data="",
                    ),
                    # Reference dropdown
                    html.Div(
                        style={
                            "marginBottom": "1.5rem",
                        },
                        children=[
                            html.Label(
                                "Selecteer:",
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
                                clearable=False,
                                style={
                                    "maxWidth": "500px",
                                },
                            ),
                        ],
                    ),
                    # Two-column section
                    html.Div(
                        style={
                            "display": "flex",
                            "gap": "1.5rem",
                            "marginBottom": "1rem",
                        },
                        children=[
                            # Left column
                            html.Div(
                                style={
                                    "flex": "1",
                                },
                                children=[
                                    html.H3(
                                        "Meegestuurde context",
                                        style={
                                            "marginBottom": "0.5rem",
                                        },
                                    ),
                                    html.Div(
                                        id="context-text",
                                        children=[],
                                        className="p-3 bg-light border rounded",
                                        style={
                                            "height": "400px",
                                            "minHeight": "150px",
                                            "resize": "vertical",
                                            "overflowY": "auto",
                                            "fontSize": "1.05rem",
                                            "lineHeight": "1.8",
                                            "userSelect": "text",
                                            "cursor": "text",
                                            "whiteSpace": "pre-wrap",
                                        },
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "gap": "0.5rem",
                                            "marginTop": "0.8rem",
                                        },
                                        children=[
                                            dbc.Button(
                                                "Markeer als gemiste informatie",
                                                id="missing-btn",
                                                n_clicks=0,
                                                style={
                                                    "backgroundColor": (
                                                        HighlightStyle.MISSING.color
                                                    ),
                                                    "borderColor": (
                                                        HighlightStyle.MISSING.color
                                                    ),
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
                            # Right column
                            html.Div(
                                style={
                                    "flex": "1",
                                },
                                children=[
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justifyContent": "space-between",
                                            "alignItems": "center",
                                        },
                                        children=[
                                            html.H3(
                                                "LLM Resultaat",
                                                style={"margin": "0"},
                                            ),
                                            html.Div(
                                                style={
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "gap": "0.4rem",
                                                },
                                                children=[
                                                    html.Label(
                                                        "Bruikbaarheid:",
                                                        htmlFor="usability-score",
                                                        style={
                                                            "fontSize": "0.8rem",
                                                            "fontWeight": "600",
                                                            "margin": "0",
                                                        },
                                                    ),
                                                    dbc.RadioItems(
                                                        id="usability-score",
                                                        options=[
                                                            {
                                                                "label": str(i),
                                                                "value": i,
                                                            }
                                                            for i in range(1, 6)
                                                        ],
                                                        value=None,
                                                        className="btn-group",
                                                        inputClassName="btn-check",
                                                        labelClassName="btn btn-"
                                                        "outline-primary",
                                                        labelCheckedClassName="active",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        id="llm-text",
                                        children=[],
                                        className="p-3 bg-light border rounded",
                                        style={
                                            "height": "400px",
                                            "minHeight": "150px",
                                            "resize": "vertical",
                                            "overflowY": "auto",
                                            "fontSize": "1.05rem",
                                            "lineHeight": "1.8",
                                            "userSelect": "text",
                                            "cursor": "text",
                                            "whiteSpace": "pre-wrap",
                                        },
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "gap": "0.5rem",
                                            "marginTop": "0.8rem",
                                            "flexWrap": "wrap",
                                        },
                                        children=[
                                            dbc.Button(
                                                "Markeer als fout",
                                                id="error-btn",
                                                n_clicks=0,
                                                style={
                                                    "backgroundColor": (
                                                        HighlightStyle.ERROR.color
                                                    ),
                                                    "borderColor": (
                                                        HighlightStyle.ERROR.color
                                                    ),
                                                },
                                            ),
                                            dbc.Button(
                                                "Markeer als triviale informatie",
                                                id="trivial-btn",
                                                n_clicks=0,
                                                style={
                                                    "backgroundColor": (
                                                        HighlightStyle.TRIVIAL.color
                                                    ),
                                                    "borderColor": (
                                                        HighlightStyle.TRIVIAL.color
                                                    ),
                                                },
                                            ),
                                            dbc.Button(
                                                "Markeer als verkeerde formulering",
                                                id="wording-btn",
                                                n_clicks=0,
                                                style={
                                                    "backgroundColor": (
                                                        HighlightStyle.WORDING.color
                                                    ),
                                                    "borderColor": (
                                                        HighlightStyle.WORDING.color
                                                    ),
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
                        style={
                            "fontSize": "0.9rem",
                            "marginBottom": "0.5rem",
                        },
                    ),
                    html.Div(
                        id="table-container",
                        children=[
                            build_table([]),
                        ],
                        style={
                            "marginTop": "0.5rem",
                        },
                    ),
                ],
            ),
        ],
    )
