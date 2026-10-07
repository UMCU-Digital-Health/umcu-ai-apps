# Base command
COMMAND="rsconnect write-manifest dash \
--entrypoint src.umcu_ai_apps.llm_evaluation.app:app --overwrite \
--exclude logs --exclude notebooks --exclude output --exclude tests --exclude build \
--exclude .dvc --exclude .github --exclude .ruff_cache --exclude .coverage \
--exclude .pytest_cache --exclude .env --exclude .venv --exclude .vscode \
--exclude docs --exclude \"**/*.db\" --exclude \"**/*.pyc\" \
--exclude \"**/*.egg-info/*\""

# Generate requirements file
uv export --frozen -q --no-hashes --no-dev -o requirements.txt

# Execute the command
eval $COMMAND .
rm requirements.txt
