project_dir := .
bot_dir := bot

lang_dir := lang

# Lint code
.PHONY: lint
lint:
	black --check --diff $(project_dir)
	ruff $(project_dir)
	mypy $(project_dir) --strict

# Reformat code
.PHONY: reformat
reformat:
	black $(project_dir)
	ruff $(project_dir) --fix

# Update translations
.PHONY: i18n
i18n:
	poetry run i18n multiple-extract \
		--input-paths $(bot_dir) \
		--output-dir $(lang_dir) \
		-k i18n -k L --locales $(locale) \
		--create-missing-dirs

# Make database migration
.PHONY: migration
migration:
	alembic revision \
		--autogenerate \
		--rev-id $(shell python migrations/_get_next_revision_id.py) \
		--message "$(message)"

.PHONY: migrate
migrate:
	alembic upgrade head

.PHONY: rollback
rollback:
	alembic downgrade -1

.PHONY: run
run:
	python -m bot || true
