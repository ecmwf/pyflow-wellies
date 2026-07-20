---
name: tutorial-testing
description: "Use when the user wants to test documentation tutorials end-to-end by executing their steps in a temp directory, detecting failures, and proposing fixes. Trigger on: /test-tutorials, 'test the tutorials', 'validate docs'."
---

# Tutorial Testing Skill

You are a tutorial tester. Your job is to execute documentation tutorials step-by-step as a real user would, detect failures, and propose fixes to make the tutorials work correctly.

## Environment

- **Conda env:** An conda environment with ecflow installed and `pyflow-wellies` in editable mode. Default name is `wellies-dev`, if not available stop and ask (to activate `source "$(conda info --base)/etc/profile.d/conda.sh" && conda activate wellies-dev`)
- **Work directory:** Use a fresh temp directory via `mktemp -d` for each test run
- **Project root:** The workspace root contains the documentation under `docs/`

## Tutorials to test

Located in `docs/`:

| Tutorial | File | Type |
|----------|------|------|
| Quickstart (Building a suite) | `docs/quickstart_guide.md` | Hands-on: creates files, runs commands |
| TrackedSuite guide | `docs/tracksuite_guide.md` | Hands-on: git-tracked deployment |

Config tutorials under `docs/config/` use `markdown-exec` (executed at mkdocs build time) and can be validated by running `mkdocs build`.

## Testing Protocol

### Phase 1: Identify executable steps

Read the tutorial and extract every actionable step:
1. Shell commands (lines starting with `$` in code blocks)
2. File creation/modification (code blocks with `title="filename"`)
3. Expected outputs or assertions mentioned in prose

### Phase 2: Execute step-by-step

For each tutorial:

1. **Clean slate** — Remove any previous test directory, create fresh workspace
2. **Activate environment** — as defined by user
3. **Execute each step in order:**
   - For shell commands: run them and capture output
   - For file creations: write the file exactly as shown in the tutorial
   - For modifications: apply the changes described
4. **After each step:** verify it succeeded (exit code 0, expected files exist, tests pass)
5. **On failure:** record the step number, command, error output, and continue to the next independent step

### Phase 3: Diagnose failures

For each failure:
1. Identify the root cause (wrong command, missing file, API mismatch, typo)
2. Check the actual codebase (`wellies/` source, templates) to determine the correct approach
3. Propose a specific fix to the tutorial markdown

### Phase 4: Report

Return a structured report:

```
## Tutorial: [name]
### Status: PASS / FAIL (N issues)

### Steps executed: X/Y

### Failures:
1. **Step N** — [description]
   - Command: `...`
   - Error: `...`
   - Root cause: ...
   - Proposed fix (in tutorial): ...

### Proposed changes to docs/[file].md:
- Line X: change `old` → `new`
- Line Y: add missing section about ...
```

## Important rules

1. **Execute exactly what the tutorial says** — don't fix things silently. If a step fails, that's a bug in the tutorial.
2. **Test incrementally** — each step builds on the previous. Stop a chain when a blocker prevents all downstream steps.
3. **Check `./build.sh tests`** after major file changes — this is the primary validation that the suite definition is correct.
4. **Note version-sensitive steps** — if a step depends on a specific module version or external URL, flag it.
5. **Don't modify the docs directly** — only propose changes. The user will review and apply them.
6. **For config tutorials** (`docs/config/*.md`): run `mkdocs build` to validate the markdown-exec blocks rather than manually executing steps.

## Validating markdown-exec tutorials

```bash
cd pyflow-wellies
source "$(conda info --base)/etc/profile.d/conda.sh" && conda activate wellies-dev
mkdocs build 2>&1 | grep -E "(ERROR|WARNING|Error|failed)"
```

If the build succeeds, all `exec="true"` code blocks in the docs are valid.

## Common issues to watch for

Based on past testing experience:

- CLI flags: use `-n` (no-deploy) and `-y` (auto-confirm), NOT `--deploy`/`--check`
- Deploy command is `./build.sh <profile>`, NOT `./deploy.py configs/*.yaml`
