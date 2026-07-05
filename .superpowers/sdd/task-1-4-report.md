# Task 1-4 Bootstrap Report

Implemented the bootstrap package for `haiku-scribe` across Tasks 1 through 4.

## Delivered

- Added packaging metadata in `pyproject.toml` with `src/` layout and a `haiku-scribe` console script.
- Created the package skeleton: `__init__.py`, `__main__.py`, and `cli.py`.
- Added the static contract layer in `contracts.py` and path resolution in `paths.py`.
- Added settings merge helpers in `settings.py` and owned Markdown block helpers in `markdown_blocks.py`.
- Added backup and setup orchestration in `backups.py` and `setup.py`.
- Added and updated the test coverage for CLI routing, contracts, settings, and markdown block behavior.

## Behavior

- `python -m haiku_scribe` routes `setup`, `doctor`, and `uninstall`.
- `setup --dry-run --home PATH` prints planned actions without writing files.
- `setup --home PATH` writes the agent, guidance, and settings files under the user-scoped `.claude` directory.
- Existing guidance and settings files are backed up before being changed.
- Guidance blocks are inserted/replaced using the owned markers so repeated runs stay idempotent.
- Default deny rules are merged without duplicating existing entries.

## Verification

- `python3 -m compileall src tests`
- `python3 -m pytest tests/test_cli_setup.py tests/test_settings.py tests/test_markdown_blocks.py -v`
- `python3 -m pytest -v`

## Notes

- The container did not have `pytest` available initially, so it was installed into user site-packages to run the requested test suite.
- The editable install was required so the subprocess-based CLI tests could resolve `python -m haiku_scribe` from the repo root.

## Review Fix Verification

- `python3 -m pytest tests/test_markdown_blocks.py tests/test_cli_setup.py`
- `python3 -m pytest tests/test_markdown_blocks.py -q`
- Result: 10 passed, covering block-preservation behavior and clean-checkout CLI subprocess imports.
