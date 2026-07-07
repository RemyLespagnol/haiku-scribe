# Plan : rendre Haiku Scribe réellement utilisable par d'autres

Date : 2026-07-07
Statut : proposé (session Fable autonome)
Entrées : roadmap 2026-07-04, TODO.md, sweep break-even 2026-07-06, survey repo (72 tests verts, ruff clean, bench OK)

## Diagnostic

Le V1 est sain : installer idempotent, testé, réversible, MIT, README honnête. Deux problèmes bloquent l'usage réel par d'autres :

1. **La valeur cœur n'est pas prouvée positive.** Le sweep montre que la délégation coûte parfois +50% (tâche détail sur gros fichier : le main délègue *puis* relit tout). Distribuer plus large maintenant, c'est distribuer un produit qui peut coûter de l'argent à l'utilisateur.
2. **La distribution est trop lourde.** `git clone` + venv + `pip install -e .` pour installer... un fichier markdown d'agent et un bloc de guidance. En 2026, la surface naturelle Claude Code est le **plugin** (`/plugin install`, marketplace) : un plugin livre nativement `agents/`, hooks et skills, versionné, désinstallable proprement. La roadmap met le plugin en V3 après V2 (team mode) — pour un projet solo OSS, c'est inversé : le plugin EST la distribution personnelle. V2 team mode devient largement inutile (un plugin se partage par nature).

## Décision de roadmap (amendement)

- **Avancer V3 (plugin) avant V2 ; V2 (team mode) est probablement absorbé par le plugin — à réévaluer après.**
- V1.3 (soft enforcement) : gelé, non justifié par les données.
- `extract` : abandonné (YAGNI, lmsgo le fait déjà).
- Audit dashboard complet (v1.1) : gelé, le micro-log JSONL suffit.

## Phase A — Corriger la valeur cœur (P0, avant toute distribution)

1. **Sortie scout substituable** (TODO P0 existant). Renforcer le contrat agent dans `contracts.py` : quand la tâche demande stats/comptages/occurrences ordonnées/corrélations, le scout doit retourner l'extraction exacte (valeurs, paths + lignes), pas un résumé. Gate : re-run du cas 10k-lignes-détail du sweep → plus de double lecture, coût scout ≤ raw.
2. **Politique de triggers V1.2 réelle** : triggers FR/EN réalistes (`état du projet`, `audit`, `cartographie`, `plusieurs fichiers`...) + tests positifs/négatifs multilingues avant tout élargissement. (Deux items TODO P0 fusionnés.)
3. **Hook dégradable prouvé** : tests payloads malformés / events inconnus → exit 0 silencieux.

Gate de phase : le bench montre moins de tokens bruts dans la session principale sans perte de justesse, sur au moins les cas du sweep.

## Phase B — Distribution : plugin Claude Code (le vrai « utilisable par d'autres »)

4. **Packager en plugin** : `.claude-plugin/plugin.json` + `agents/haiku-scribe.md` + bloc de guidance (skill ou CLAUDE.md fragment) + hooks opt-in. Le contenu généré existe déjà comme littéraux dans `contracts.py`/`v1_2_hooks.py` — le plugin est une deuxième cible de rendu, pas une réécriture. Le CLI Python reste pour `doctor` et les power users. Spec dédiée : `v3-plugin-packaging-design.md` (allégée).
5. **Hygiène release** : champ `license` + classifiers dans `pyproject.toml` ; notes de release ; tag `v0.1.0`. Marketplace entry (repo GitHub public suffit).
6. **Petits fixes UX installeur** : `setup --dry-run` honnête après install ; wording `uninstall` (fichier supprimé vs contenu retiré) ; cacher ou documenter `prototype-hooks`.

Gate de phase : un inconnu installe via `/plugin install`, l'agent apparaît, la délégation se déclenche sur un cas réel, désinstallation propre.

## Phase C — Mesure minimale (après adoption, pas avant)

7. **`haiku-scribe report` minimal** : agrégation du JSONL de nudges existant (`--since`, `--json`). Seulement si les hooks opt-in sont réellement utilisés.
8. Checklist de smoke test manuel dans les docs (setup, doctor, agent visible, nudge, uninstall).

## Ce qu'on ne fait pas (et pourquoi)

- `extract`, MCP, CodeGraph dans l'agent de base, enforcement `PreToolUse`, dashboard d'audit, mode enterprise : soit YAGNI, soit non justifiés par les données du sweep, soit après preuve d'adoption.

## Ordre d'exécution recommandé

A1 → A2 → (A3 en parallèle) → bench de validation → B4 → B5/B6 → tag → C seulement si usage réel.
