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

### 3. Triage each stub: keep, exclude, or dedupe

Not every auto-stubbed slug is a real benchmark worth listing. Before researching, decide for each stub whether it should be **kept** (→ research + fill, the common case), **excluded** (junk), or **deduped** (a copy of one we already list). Excluded/deduped slugs go in `docs/exclude.yml` instead of getting `categories` filled in.

> The live scrape in step 6 (`validate_overrides.py`) often surfaces *more* new slugs than the PR description lists — datasets land on the hub after the nightly bot ran. Triage those the same way. Run validate early to see the full set.

**Exclude experimental / personal junk.** People push half-finished or personal tasks to the hub that aren't published benchmarks. Tells:
- Slug looks like a working file, not a release: `task1_v3_1_...`, `..._train_patched` / `..._eval_patched`, version/scratch suffixes (`-v1`, `-rolling`).
- `desc` reads like an internal dev note, e.g. `"Patched verifier rebuild: reworked Modal capability-contract checks ... Tasks identical except tests/verify.py."`
- Tiny task count (a handful of samples) with a generic name.
- The org is an **individual**, not a project/company. Check it:
  ```bash
  gh api users/<org> -q '.type + " | " + (.name // "") + " | repos=" + (.public_repos|tostring)'
  ```
  `type=User` (a person) with no matching benchmark repo is a strong exclude signal; `type=Organization` (or a User whose repo *is* the canonical benchmark) is a keep signal. A slug whose org doesn't resolve at all (`404`) and reads like a dev artifact is junk.

When in doubt about whether something is a real benchmark vs. junk, ask the user before excluding.

**Dedupe copies published under multiple orgs.** The same benchmark sometimes appears under several org slugs (verbatim re-uploads). Keep the copy from the **most credible / original author** — the benchmark's actual authors, or the org that owns the upstream GitHub repo — and exclude the rest. Confirm they're really the same before dropping one:
```bash
uv run python -c "
from inspect_harbor import <func_a>, <func_b>
a, b = <func_a>().dataset, <func_b>().dataset
print('counts:', len(a), len(b))
print('inputs identical:', sorted(s.input for s in a) == sorted(s.input for s in b))
"
```
Identical inputs (even if sample ids are renamed) ⇒ duplicate. Example: `xiaoboai/pawbench` is a verbatim copy of `agentscope-ai/pawbench` (same 150 inputs, renamed ids) — we keep `agentscope-ai` (the author org that owns the PawBench repo) and exclude `xiaoboai/pawbench`.

**How to exclude.** Add a glob to `docs/exclude.yml` with a one-line comment saying *why*, prefer an org-wide glob (`ashantanu/*`, `vmax-modal/*`) for a junk account and an exact slug (`xiaoboai/pawbench`) for a single dedup. Then drop any stub the bot already added to `docs/overrides.yml` (pop it in the helper from step 5, or it'll linger as an orphan-warning). After regenerating, the slug disappears from `_tasks.py` and the listing. See the header of `docs/exclude.yml` for the existing patterns.

### 4. Research each new dataset

For each slug you're keeping, gather:

| Field | Where to find it |
|---|---|
| `categories` | Required. Pick 1–2 from the vocabulary in `docs/overrides.yml`'s header (`Coding`, `Reasoning`, `Law`, `Multimodal`, …). See "Category picking" below. |
| `title` | Canonical branding. Strongly suggested when the auto-derived form (just the slug suffix) is wrong-cased or non-obvious. |
| `repo` | Canonical upstream GitHub URL. Almost always exists for benchmarks. |
| `arxiv` | Paper URL if the benchmark has one. Many don't (especially newer ones). |
| `desc` | **Read it for every slug you touch, but prefer Harbor's default.** Only override when the default is useless (a placeholder or bare restatement of the slug, e.g. `ivanleo/agent-search` ships `"Evaluation dataset for agent-search task."`), missing entirely, or extremely long. Length alone is usually fine — the listing table uses `desc_trunc`. See "Writing descriptions" below. |

**Order of operations for research:**

1. Check `docs/registry-listing.yml` for the slug — it carries Harbor's own `desc` field. That's often enough context for categorization, and the default `desc` is usually fine to publish as-is. **Read it, though** — it's surfaced on the registry listing and the AISI evals browser, so if it's a useless placeholder (or missing), plan to override it. See "Writing descriptions" below.
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

**Writing descriptions:**

Read the `desc` for every slug you're filling in categories for — it's published verbatim on the registry listing and the AISI evals browser. But **prefer Harbor's default**: only write your own when the default is useless (a placeholder or bare restatement of the slug, like `"Evaluation dataset for agent-search task."`), absent, or extremely long. Length on its own isn't a reason — the table layout falls back to `desc_trunc`, so a long-but-informative default can stay.

When you do rewrite, aim for one sentence that says **what the model is asked to do and in what domain** — concrete enough that a reader scanning the listing knows whether the benchmark is relevant. If the default is uninformative, inspect a task input (the one-liner above) to learn what the task really is, then write from that. Example: for `ivanleo/agent-search`, the task loads a docs SQLite DB and asks the agent to answer API questions by writing queries — so a fitting `desc` is `"Agent answers Gemini API questions by querying an indexed documentation database."` rather than the shipped placeholder.

### 5. Apply the overrides

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

### 6. Validate, regenerate, format, test

```bash
uv run python scripts/validate_overrides.py    # CI's gate; must report all valid
uv run python scripts/generate_tasks.py        # regen _tasks.py + listing + per-dataset .qmd
make check                                     # ruff (fixes _tasks.py docstring formatting)
uv run pytest tests/ --no-header               # 167+ tests; should be 100% pass
```

### 7. Commit and push

The bot's own commit on the branch already says `fix: update Harbor registry tasks`. Your commit can be the same or `fix: fill in categories for <new datasets>`. Push to `origin update-harbor-tasks`.

### 8. After merge: publish the docs site

The user merges the PR. Docs at https://meridianlabs-ai.github.io/inspect_harbor are not auto-published — the new datasets won't show up on the registry listing until someone re-renders + pushes `gh-pages`. Do it as soon as the merge lands so the public docs catch up:

```bash
git switch main
git pull --ff-only
cd docs
PRE_COMMIT_ALLOW_NO_CONFIG=1 uv run quarto publish gh-pages --no-prompt
```

The `PRE_COMMIT_ALLOW_NO_CONFIG=1` env var is needed because the user has a global pre-commit hook that blocks the gh-pages worktree (which has no `.pre-commit-config.yaml`). Without it the publish renders successfully but the final commit fails silently and the remote `gh-pages` stays unchanged.

GitHub Pages cache can take a few minutes after the push.

## Gotchas

### The scraper regex breaks when Harbor changes hub HTML

Symptom: `scripts/generate_tasks.py` errors with `Scrape returned only 0 slug(s) (expected ≥ 50)`. Min-slug guard is doing its job — it'd otherwise orphan-drop every override.

Cause: Harbor changes the hub's HTML format (e.g. moves from SSR `href="/datasets/..."` attrs to client-state JSON `\"href\":\"/datasets/...\"`).

Fix: loosen the regex in `scrape_hub_slugs()` to match any `/datasets/<org>/<name>` occurrence, dropping the `href=` quote requirement. The character class `[A-Za-z0-9_.-]+` (no `/`) makes the match stop at the right boundary regardless of surrounding syntax.

### `_tasks.py` docstring whitespace churn

Regenerating sometimes produces a `_tasks.py` diff where continuation lines lose 4-space indents (e.g. on multi-line descriptions like `rexbench`). This is pre-existing — `make check` (which runs `ruff format`) re-applies the indent. Don't try to fix this in the template; just run `make check` and commit the result.

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