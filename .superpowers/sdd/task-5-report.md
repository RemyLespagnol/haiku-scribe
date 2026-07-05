# Task 5 Report: Doctor Diagnostics

Implemented the doctor diagnostics flow for Haiku Scribe.

## Changes

- Added `src/haiku_scribe/doctor.py` with:
  - `DoctorResult(ok: bool, failures: list[str])`
  - `doctor_user(home: Path) -> DoctorResult`
  - checks for:
    - missing agent file
    - agent drift from the required `haiku-scribe` metadata and read-only tool set
    - missing `CLAUDE.md` guidance block
    - missing settings file
    - missing deny rules in `settings.json`
- Updated `src/haiku_scribe/cli.py` so `haiku-scribe doctor` prints success/failure output and exits with the right status code.
- Added `tests/test_doctor.py` covering:
  - successful doctor run after setup
  - missing installation
  - agent model drift
  - missing deny rule

## Verification

- `python3 -m pytest tests/test_doctor.py -v`
- `python3 -m pytest tests/test_cli_setup.py -v`
- `python3 -m pytest tests -v`

All tests passed.
