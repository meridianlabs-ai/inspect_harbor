---
name: nightly-pr-triage
description: Triage the nightly auto-update PR for the Harbor registry — fill in categories, title, repo, arxiv on newly-stubbed `docs/overrides.yml` entries so CI passes and the docs/AISI evals browser surface the dataset with proper branding.
---

# Nightly PR triage

A scheduled GitHub Action (`.github/workflows/update-registry.yml`) runs every night, scrapes `hub.harborframework.com/datasets`, regenerates `src/inspect_harbor/_tasks.py` and `docs/registry-listing.yml`, and opens a PR titled `fix: update Harbor registry tasks` on the `update-harbor-tasks` branch. When new datasets appeared upstream, the bot auto-stubs them in `docs/overrides.yml` with `categories: []`. A human (you) needs to fill in real values before merge — `scripts/validate_overrides.py` runs in CI and blocks the merge on empty stubs.

## Steps

### 1. Find and check out the PR

```bash
gh pr list --repo meridianlabs-ai/inspect_harbor --search "update Harbor registry tasks" --state open
```

Check out cleanly — the bot force-pushes to `update-harbor-tasks` so a stale local copy will fail to fast-forward. Always reset first:

```bash
git switch main
git pull --ff-only
git branch -D update-harbor-tasks 2>/dev/null || true
gh pr checkout <pr-number> --repo meridianlabs-ai/inspect_harbor
```

### 2. Identify newly-stubbed slugs

The PR description lists them under "Action required: fill in categories for new datasets". Or pull from the diff directly:

```bash
git diff main..HEAD docs/overrides.yml | grep -B1 "categories: \[\]"
```

Each newly-stubbed entry looks like:

```yaml
org/name:
  categories: []
```

### 3. Research each new dataset

For each slug, gather:

| Field | Where to find it |
|---|---|
| `categories` | Required. Pick 1–2 from the vocabulary in `docs/overrides.yml`'s header (`Coding`, `Reasoning`, `Law`, `Multimodal`, …). See "Category picking" below. |
| `title` | Canonical branding. Strongly suggested when the auto-derived form (just the slug suffix) is wrong-cased or non-obvious. |
| `repo` | Canonical upstream GitHub URL. Almost always exists for benchmarks. |
| `arxiv` | Paper URL if the benchmark has one. Many don't (especially newer ones). |
| `desc` | Override only if Harbor's metadata description is unclear or too long for the listing layout (>100 chars truncates). |

**Order of operations for research:**

1. Check `docs/registry-listing.yml` for the slug — it carries Harbor's own `desc` field. That's often enough context.
2. Look at sibling entries in `docs/overrides.yml` (same `org/...` prefix, or same benchmark family) for naming/category patterns. Example: when `scale-ai/swe-atlas-rf` got auto-stubbed, sibling `scale-ai/swe-atlas-qna` and `scale-ai/swe-atlas-tw` already had `Coding` + `repo: https://github.com/scaleapi/SWE-Atlas` + `title: SWE-Atlas (QnA)` / `(Test Writing)` — same pattern applied directly.
3. WebSearch (`<benchmark name> github`) when the brand or repo isn't obvious from the description. Skip this for self-evident names.
4. Use `gNucleus AI` / `Harvey AI` style company-and-benchmark phrasing when both matter for findability.
5. **When the domain is ambiguous, inspect a task input directly.** Load one sample and read its prompt — descriptions can mislead. Example: `gnucleus-ai/cad-bench`'s description says "100 parametric FreeCAD tasks" which sounds like pure CAD/Professional. The actual task prompt is "*Write a FreeCAD Python script to `answer.py` that reproduces the part described below*" — so it's code-gen into a CAD domain → `[Coding, Professional]`, not `[Professional]` alone. The one-liner:
   ```bash
   uv run python -c "from inspect_harbor import <func_name>; t = <func_name>(n_tasks=1); print(repr(t.dataset[0].input[:300]))"
   ```

**Category picking:**

The canonical vocabulary lives at the top of `docs/overrides.yml`. Mirror it in `scripts/validate_overrides.py:CATEGORY_VOCAB` and inspect_ai's `docs/evals/sync.py:CATEGORY_VOCAB` (we don't own this — `inspect_ai` does — so don't invent new categories without coordinating with them).

Common mappings:
- Code-generation / agent benchmarks → `Coding`
- Math, reasoning puzzles → `Reasoning` (use `Mathematics` only for explicit math content like AIME)
- Legal, finance, medicine → `Law` / `Finance` / `Medicine` (often paired with `Professional`)
- Vision/text-multimodal → `Multimodal`
- Safety/jailbreak → `Safeguards`
- Cybersecurity → `Cybersecurity`

Use a secondary category when the benchmark spans clear domains (e.g. `MichaelY310/devopsgym` is `[Coding, Professional]` because DevOps is both code and a professional domain). Don't pile on for breadth — 1–2 strong categories beat 4 weak ones.

**Title styling:**

- Match the project's own canonical capitalization (`AIME`, `GAIA`, `USACO`, `BFCL`, `RExBench`, `SimpleQA`).
- Use parens for splits: `KUMO (easy)`, `SWE-Lancer Diamond (Manager)`, `Reasoning Gym (hard)`.
- Hyphens stay; spaces are for words: `SWE-bench Verified`, `DevOps-Gym`, `Terminal-Bench v2`.
- Greek/Unicode is fine if it's the project's own form: `τ³-bench` for `sierra-research/tau3-bench`.
- Skip the override when the leaf slug is already a clean display name (e.g. `runebench`, `vmax-tasks`).

### 4. Apply the overrides

Use the in-script helpers — they preserve the file's header comment and field order:

```bash
uv run python -c "
import sys
sys.path.insert(0, 'scripts')
from generate_tasks import load_overrides, write_overrides_file
overrides = load_overrides()
overrides['org/name'] = {
    'categories': ['Coding'],
    'title': 'Pretty Name',
    'repo': 'https://github.com/org/repo',
    # 'arxiv': 'https://arxiv.org/abs/...',
}
write_overrides_file(overrides)
"
```

### 5. Validate, regenerate, format, test

```bash
uv run python scripts/validate_overrides.py    # CI's gate; must report all valid
uv run python scripts/generate_tasks.py        # regen _tasks.py + listing + per-dataset .qmd
make check                                     # ruff (fixes _tasks.py docstring formatting)
uv run pytest tests/ --no-header               # 167+ tests; should be 100% pass
```

### 6. Commit and push

The bot's own commit on the branch already says `fix: update Harbor registry tasks`. Your commit can be the same or `fix: fill in categories for <new datasets>`. Push to `origin update-harbor-tasks`.

## Gotchas

### The scraper regex breaks when Harbor changes hub HTML

Symptom: `scripts/generate_tasks.py` errors with `Scrape returned only 0 slug(s) (expected ≥ 50)`. Min-slug guard is doing its job — it'd otherwise orphan-drop every override.

Cause: Harbor changes the hub's HTML format (e.g. moves from SSR `href="/datasets/..."` attrs to client-state JSON `\"href\":\"/datasets/...\"`).

Fix: loosen the regex in `scrape_hub_slugs()` to match any `/datasets/<org>/<name>` occurrence, dropping the `href=` quote requirement. The character class `[A-Za-z0-9_.-]+` (no `/`) makes the match stop at the right boundary regardless of surrounding syntax.

### `_tasks.py` docstring whitespace churn

Regenerating sometimes produces a `_tasks.py` diff where continuation lines lose 4-space indents (e.g. on multi-line descriptions like `rexbench`). This is pre-existing — `make check` (which runs `ruff format`) re-applies the indent. Don't try to fix this in the template; just run `make check` and commit the result.

### Pre-commit hook complains during `quarto publish gh-pages`

If the user is publishing docs after merge, the gh-pages worktree has no `.pre-commit-config.yaml` and a global pre-commit hook blocks the commit. Workaround: `PRE_COMMIT_ALLOW_NO_CONFIG=1 uv run quarto publish gh-pages`.

### Category vocabulary is owned by inspect_ai

`inspect_ai/docs/evals/sync.py:CATEGORY_VOCAB` is the source of truth. We mirror it in `scripts/validate_overrides.py:CATEGORY_VOCAB`. If you want to add a new category (e.g. `Gaming`, `DevOps`), propose it upstream in `inspect_ai` first — `sync_harbor.py` rejects unknown categories.

## Reference files

- `docs/overrides.yml` — the hand-maintained metadata, keyed by `org/name` slug. Header has full field documentation.
- `docs/registry-listing.yml` — auto-generated machine-readable listing. Has `desc` (full) and `desc_trunc` (table-friendly).
- `scripts/generate_tasks.py` — scrape + decorate + emit. Run after edits.
- `scripts/validate_overrides.py` — CI gate. Run before push.
- `scripts/_templates.py` — generated-file templates. Don't edit per-PR.
- `docs/exclude.yml` — slug patterns to skip during scraping (e.g. `openthoughts/*`).
- `.github/workflows/update-registry.yml` — the cron job that opens these PRs.