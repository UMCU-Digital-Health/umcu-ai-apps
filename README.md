# umcu-ai-apps

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Author: Laura Veerhoek
Email: l.p.veerhoek@umcutrecht.nl

## Installation

To install the umcu_ai_apps package use:

```bash
uv sync
```

## First use

To populate the database first run the prep_llm_eval command:

```bash
prep_llm_eval -p project_name data/processed/llm_evaluation_data_example.csv
```
You need to give a project name, which will be used together with the department for user authorization.
To add users and their authorization to the database (or add new projects/departments to an existing user):

```bash
add_eval_user -p project_name -d dep_a -d dep_b test@test.nl
```
Notice that you can supply multiple departments by repeating the -d flag.

Then you can run the dashboard locally in dev mode by using the llm_eval_dash command:

```bash
llm_eval_dash
```

Which opens a dash application using port 8017 on localhost
