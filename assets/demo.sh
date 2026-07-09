#!/usr/bin/env bash
# Faux haiku-scribe session, printed (not executed) for the README demo GIF.
# Rendered via demo.tape — see the Development note in README.
printf '\033[2J\033[3J\033[H'   # clear screen + scrollback so the launch command isn't shown
sleep 0.6
printf '\033[38;5;146m❯\033[0m map how auth flows across the files that touch login\n'
sleep 0.9
printf '\033[38;5;108m· Delegating the survey to haiku-scribe (read-only Haiku scout)…\033[0m\n'
sleep 1.1
printf '\033[38;5;114m✓ Brief returned — 8 files read, coverage complete\033[0m\n'
sleep 0.6
printf '\n'
printf '  \033[1mSummary\033[0m\n'
printf '  login → routes/auth.py:42 → services/session.py\n'
printf '  bcrypt check :88 · JWT minted :140 · 2 callers bypass the service\n'
sleep 2.6
