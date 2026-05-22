---
name: finrlx-handoff-evidence-packager
description: Produces review-ready evidence at the close of every FINRLX UX phase. Activates at the end of any phase from Phase 1 onward. Generates the phase report, captures the changed-file list, copies screenshots, runs the review-package zip command, and records git status / SHA. Never marks a phase "shipped" with a missing artifact.
type: project
---

# FINRLX — Handoff Evidence Packager

## When to invoke

- At the close of every phase from Phase 1 onward.
- Whenever the user asks for "a review package" or "an evidence drop".

## Required outputs per phase

For phase N, produce all of the following under `DOCS/handoff/`:

1. **Phase report.** `DOCS/handoff/FINRLX_UX_PHASE_{N}_REPORT.md`, following the master plan §6 template (sections A–K).
2. **Changed-file list.** `DOCS/handoff/FINRLX_UX_PHASE_{N}_CHANGED_FILES.txt`, generated from `git diff --name-only <baseline>..HEAD`. Use the previous phase's commit SHA (or `main` if no prior phase) as baseline.
3. **Test evidence.** `DOCS/handoff/FINRLX_UX_PHASE_{N}_TEST_OUTPUT.txt` — verbatim stdout/stderr from the visual-qa-gate skill's commands. Truncate any single command's output to the first 200 + last 100 lines if longer than 500.
4. **Screenshot evidence.** `DOCS/handoff/screenshots/phase{N}/` directory of PNGs from the screenshot matrix. If the matrix could not run, this file: `DOCS/handoff/screenshots/phase{N}/_NOT_CAPTURED.md` with verbatim error.
5. **Known limitations.** `DOCS/handoff/FINRLX_UX_PHASE_{N}_KNOWN_GAPS.md` — short bullet list of what was left undone and why.

## Review-package command (PowerShell, Windows-host)

```powershell
$ErrorActionPreference = "Stop"
$root = Get-Location
$phase = "{N}"   # set per call
$stage = Join-Path $root "_review_package_ux_phase${phase}"
$zip = Join-Path $root "FINRLX_ux_phase${phase}_review_package.zip"

if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
if (Test-Path $zip) { Remove-Item $zip -Force }
New-Item -ItemType Directory -Path $stage | Out-Null

$dirs = @("frontend","backend","DOCS","docs","design",".claude","tests","scripts","infra")
foreach ($d in $dirs) {
    if (Test-Path $d) {
        robocopy $d (Join-Path $stage $d) /E `
            /XD node_modules .next dist build coverage .git .venv venv __pycache__ .pytest_cache .mypy_cache .idea .vscode tmp temp backups research `
            /XF *.log *.zip *.tar *.gz *.rar *.7z *.pyc *.sqlite *.sqlite3 *.db *.parquet *.pkl *.joblib `
            | Out-Null
    }
}

$files = @("package.json","package-lock.json","pnpm-lock.yaml","yarn.lock","next.config.js","next.config.mjs","tailwind.config.js","tailwind.config.ts","tsconfig.json","README.md","pyproject.toml","pytest.ini","alembic.ini","docker-compose.yml","Dockerfile",".env.example")
foreach ($f in $files) { if (Test-Path $f) { Copy-Item $f (Join-Path $stage $f) -Force } }

$meta = Join-Path $stage "_review_metadata"
New-Item -ItemType Directory -Path $meta | Out-Null
git status --short  | Out-File (Join-Path $meta "git_status_short.txt") -Encoding utf8
git diff --name-only | Out-File (Join-Path $meta "git_diff_name_only.txt") -Encoding utf8
git diff --stat       | Out-File (Join-Path $meta "git_diff_stat.txt") -Encoding utf8
git rev-parse --short HEAD | Out-File (Join-Path $meta "git_head_short.txt") -Encoding utf8

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip -Force
Write-Host "Created Phase $phase review package: $zip"
```

Substitute `{N}` per invocation.

## Bash equivalent for non-Windows hosts

```bash
phase=$1
stage="_review_package_ux_phase${phase}"
zip="FINRLX_ux_phase${phase}_review_package.zip"
rm -rf "$stage" "$zip"
mkdir -p "$stage"
for d in frontend backend DOCS docs design .claude tests scripts infra; do
  [ -d "$d" ] && rsync -a \
    --exclude node_modules --exclude .next --exclude dist --exclude build \
    --exclude coverage --exclude .git --exclude .venv --exclude venv \
    --exclude __pycache__ --exclude .pytest_cache --exclude .mypy_cache \
    --exclude .idea --exclude .vscode --exclude tmp --exclude temp \
    --exclude backups --exclude research \
    --exclude '*.log' --exclude '*.zip' --exclude '*.tar*' --exclude '*.7z' \
    --exclude '*.pyc' --exclude '*.sqlite*' --exclude '*.db' --exclude '*.parquet' --exclude '*.pkl' --exclude '*.joblib' \
    "$d/" "$stage/$d/"
done
for f in package.json package-lock.json pnpm-lock.yaml yarn.lock next.config.js next.config.mjs tailwind.config.js tailwind.config.ts tsconfig.json README.md pyproject.toml pytest.ini alembic.ini docker-compose.yml Dockerfile .env.example; do
  [ -f "$f" ] && cp "$f" "$stage/"
done
mkdir -p "$stage/_review_metadata"
git status --short  > "$stage/_review_metadata/git_status_short.txt"
git diff --name-only > "$stage/_review_metadata/git_diff_name_only.txt"
git diff --stat       > "$stage/_review_metadata/git_diff_stat.txt"
git rev-parse --short HEAD > "$stage/_review_metadata/git_head_short.txt"
( cd "$stage" && zip -qr "../$zip" . )
echo "Created Phase $phase review package: $zip"
```

## Anti-patterns

- Claiming a phase shipped without the changed-file list.
- Producing the zip but not the report.
- Pasting partial test output. Either truncate explicitly (with a "trimmed" marker) or include it all.
- Producing a screenshot directory while one of the breakpoints failed to capture, with no `_NOT_CAPTURED.md` note.

## Output discipline

The packager skill does not interpret findings. It records them. Interpretation lives in the phase report's "K. Next recommended phase" section, authored by the redesign director.
