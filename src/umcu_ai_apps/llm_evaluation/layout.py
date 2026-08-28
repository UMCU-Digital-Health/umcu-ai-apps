import dash_bootstrap_components as dbc
from dash import dcc, html

from umcu_ai_apps.llm_evaluation.helper import (
    HIGHLIGHT_STYLING,
    build_table,
)


def get_navbar(header_title: str, view_user: bool) -> dbc.NavbarSimple:
    """Create and return a Bootstrap navbar.

    Parameters
    ----------
    view_user : bool
        Whether to display the logged in user information.

    header_title : str
        The title to display in the navbar.

    Returns
    -------
    dbc.NavbarSimple
        The created navbar.
    """
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(
                html.Div(
                    id="logged_in_user",
                    className="text-white me-5",
                )
            )
            if view_user
            else None,
        ],
        brand=[
            html.Img(
                src="https://www.umcutrecht.nl/images/logo-umcu.svg",
                className="mb-2",
            ),
            header_title,
        ],
        color="#1191fa",
        dark=True,
        id="navbar",
    )

    return navbar


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
                                options=dropdown_options,
                                value=(
                                    dropdown_options[0]["value"]
                                    if dropdown_options
                                    else None
                                ),
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
                                        id="source-text",
                                        children=[],
                                        className="p-3 bg-light border rounded",
                                        style={
                                            "height": "400px",
                                            "overflowY": "auto",
                                            "fontSize": "1.05rem",
                                            "lineHeight": "1.8",
                                            "userSelect": "text",
                                            "cursor": "text",
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
                                                id="save-btn",
                                                n_clicks=0,
                                                style={
                                                    "backgroundColor": HIGHLIGHT_STYLING[
                                                        "missing"
                                                    ]["color"],
                                                    "borderColor": HIGHLIGHT_STYLING[
                                                        "missing"
                                                    ]["color"],
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
                                    html.H3(
                                        "LLM Resultaat",
                                        style={
                                            "marginBottom": "0.5rem",
                                        },
                                    ),
                                    html.Div(
                                        id="source-text-errors",
                                        children=[],
                                        className="p-3 bg-light border rounded",
                                        style={
                                            "height": "400px",
                                            "overflowY": "auto",
                                            "fontSize": "1.05rem",
                                            "lineHeight": "1.8",
                                            "userSelect": "text",
                                            "cursor": "text",
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
                                                    "backgroundColor": HIGHLIGHT_STYLING[
                                                        "error"
                                                    ]["color"],
                                                    "borderColor": HIGHLIGHT_STYLING[
                                                        "error"
                                                    ]["color"],
                                                },
                                            ),
                                            dbc.Button(
                                                "Markeer als triviale informatie",
                                                id="trivial-btn",
                                                n_clicks=0,
                                                style={
                                                    "backgroundColor": HIGHLIGHT_STYLING[
                                                        "trivial"
                                                    ]["color"],
                                                    "borderColor": HIGHLIGHT_STYLING[
                                                        "trivial"
                                                    ]["color"],
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
