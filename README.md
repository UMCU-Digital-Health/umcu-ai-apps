# umcu-ai-apps

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

General repository for apps built by the UMC Utrecht AI team.

Email: datascience@umcutrecht.nl

## Apps

| App | Description | Entry point |
|---|---|---|
| **LLM Evaluatie Applicatie** | Dash app in which clinicians evaluate LLM-generated text against the context that was sent to the model: they annotate missing information, errors, trivial information and wording issues, and give a usability score (1–5). | `src/umcu_ai_apps/llm_evaluation/app.py` |

## Documentation

Full documentation (in Dutch) lives in [`docs/`](docs/) and is built with
[MkDocs](https://www.mkdocs.org/) + [Material](https://squidfunk.github.io/mkdocs-material/):

- [User guide](docs/user-guide/llm-evaluation.md): how to use the evaluation app
- [CLI tools](docs/developer-guide/cli.md): loading data, managing users, running locally

Preview the docs locally:

```bash
uvx --from "mkdocs<2" --with mkdocs-material mkdocs serve
```

Then open <http://localhost:8000>.

## Installation

Requires Python >= 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env_example .env
```

Set `DB_ENVIRONMENT` in `.env`:

- `DEBUG`: local SQLite database (`./sql_app.db`), no further configuration needed
- `ACC` / `PROD`: MS SQL Server, fill in the `DB_*` variables for that environment

## Quick start (local)

```bash
# 1. Load the example evaluation data into the database (creates tables if needed)
uv run prep_llm_eval -p demo data/processed/llm_evaluation_data_example.csv

# 2. Give the local user access. Without Posit Connect the app sees the user as "No user"
uv run add_eval_user -p demo -d Cardiology -d Neurology "No user"

# 3. Start the app in debug mode on http://localhost:8017
uv run llm_eval_dash
```

To start over with an empty local database, delete `sql_app.db`.

## CLI tools

| Command | Purpose |
|---|---|
| `prep_llm_eval -p <project> <file.csv>` | Load evaluation data from a CSV. Existing `reference_id`s are skipped. |
| `add_eval_user -p <project> -d <department> [-d ...] <email>` | Grant a user access to a project and one or more departments. |
| `llm_eval_dash` | Run the Dash app locally (port 8017, debug mode). |

Users only see cases whose **project and department** both match one of their access
rules. Names are case-sensitive, and e-mail addresses must be entered in lower case.

The CSV needs the columns `reference_id`, `reference_description`, `department`,
`context_text`, `llm_response` and optionally `model`. See the
[CLI documentation](docs/developer-guide/cli.md) for details.

## Development

```bash
uv run ruff check .                                   # linting
uv run pytest tests/ --doctest-modules --cov=src      # tests
```

Both run in GitHub Actions on pull requests to `main`. Record changes in
[`CHANGELOG.md`](CHANGELOG.md).

## Deployment (Posit Connect)

The app is deployed to Posit Connect (`https://rsc.ds.umcutrecht.nl/`) with
`rsconnect-python`.

1. Fill in the Posit Connect variables in `.env` (`PERSONAL_API_KEY`,
   `MANIFEST_FILE_LLM_EVAL`, `APP_ID_acc`, `APP_ID_prod`, `APP_NAME_acc`,
   `APP_NAME_prod`).
2. If dependencies or files changed, regenerate the manifest:

    ```bash
    source write_manifest.sh
    mv manifest.json manifest_llm_eval.json
    ```

3. Load the variables into your shell and run the deploy script. It must be
   *sourced*, not executed:

    ```bash
    source .env
    source deploy.sh
    ```

    Choose `ACC` (1) or `PROD` (2). On a first deployment (empty `APP_ID_*`) a new
    app is created; store the returned app ID in `.env`.

`requirements.txt` is generated from `uv.lock` during deployment and is not kept in
version control. On Posit Connect, set `DB_ENVIRONMENT` and the `DB_*` variables as
environment variables of the content item.
