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
prep_llm_eval -p data/processed/llm_evaluation_data_example.csv
```

Then you can run the dashboard locally in dev mode by using the llm_eval_dash command:

```bash
llm_eval_dash
```

Which opens a dash application using port 8017 on localhost
