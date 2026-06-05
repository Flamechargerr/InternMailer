# Playwright Apply Runbook (DOCX Sources, Non-USA Internships)

## Scope
- Build internship targets from provided DOCX/ZIP source documents.
- Run 8-worker Playwright auto-apply queue with manual handling for login/CAPTCHA blocks.
- Keep Atlas as a non-blocking review dashboard mirror.

## Preconditions
- macOS Automation permission granted for Atlas control (optional but recommended).
- Playwright Chromium installed.
- Resume files available:
  - `/Users/anamay/Desktop/cv/amazon/anamay_sde_230968270.pdf`
  - `/Users/anamay/Desktop/cv/amazon/Anamay_Business_230968270.pdf`

## 1) Atlas Automation Permission
1. Open `System Settings` -> `Privacy & Security` -> `Automation`.
2. Allow your terminal app to control `ChatGPT Atlas`.

## 2) Validate Atlas Connectivity
```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export ATLAS_CLI="$CODEX_HOME/skills/atlas/scripts/atlas_cli.py"
uv run --python 3.12 python "$ATLAS_CLI" app-name
uv run --python 3.12 python "$ATLAS_CLI" tabs --json
```

## 3) Generate Tab Duplicate Reports (Optional)
```bash
python /Users/anamay/Desktop/Projects/internmailer_v3/scripts/atlas_tab_audit.py \
  --strict-live-tabs \
  --json-out /Users/anamay/Desktop/Projects/internmailer_v3/output/atlas/tab_report.json \
  --md-out /Users/anamay/Desktop/Projects/internmailer_v3/output/atlas/tab_report.md
```

Expected outputs:
- `/Users/anamay/Desktop/Projects/internmailer_v3/output/atlas/tab_report.json`
- `/Users/anamay/Desktop/Projects/internmailer_v3/output/atlas/tab_report.md`

## 4) Install Playwright Browser
```bash
python3 -m playwright install chromium
```

## 5) Build Jobs from DOCX Sources
```bash
python3 /Users/anamay/Desktop/Projects/internmailer_v3/scripts/build_jobs_from_doc_sources.py \
  --sources "/Users/anamay/Desktop/internship kimi.docx,/Users/anamay/Downloads/Kimi_Agent_Excluding USA_ Global openings.zip" \
  --non-usa-only true \
  --sectors "tech,banks,trading" \
  --output /Users/anamay/Desktop/Projects/internmailer_v3/output/jobs_doc_sources.json
```

## 6) Execute Apply Pipeline (8 Workers)
```bash
python3 /Users/anamay/Desktop/Projects/internmailer_v3/scripts/run_apply_pipeline.py \
  --resume /Users/anamay/Desktop/cv/amazon/Anamay_Business_230968270.pdf \
  --sde-resume /Users/anamay/Desktop/cv/amazon/anamay_sde_230968270.pdf \
  --business-resume /Users/anamay/Desktop/cv/amazon/Anamay_Business_230968270.pdf \
  --mode full_auto \
  --roles "SDE Intern,Data Analyst Intern,Business Analyst Intern" \
  --locations "India,Remote" \
  --non-usa-only true \
  --workers 8 \
  --blocked-flow-mode pause_for_manual_solve \
  --max-applications 10 \
  --jobs-input /Users/anamay/Desktop/Projects/internmailer_v3/output/jobs_doc_sources.json \
  --state-store /Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/queue_state.json \
  --events-out /Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/events_YYYYMMDD.jsonl \
  --results-out /Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/apply_results_YYYYMMDD.json
```

## Retry and Failure Evidence
- Retries are bounded with `--max-retries` and `--retry-delay-seconds`.
- Failure artifacts are saved under:
  - `/Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/failures/`
- Each failed or blocked run captures:
  - Screenshot (`.png`)
  - Page HTML (`.html`)

## Idempotency
- Duplicate application prevention key: `company + role + apply_url` (SHA-256).
- Persistent key store:
  - `/Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/applied_keys.json`

## Status Semantics
- `submitted`: submit completed.
- `blocked_captcha`: captcha/human challenge encountered.
- `blocked_login`: login/2FA/verification wall encountered.
- `failed_validation`: submit control or required prerequisites missing.
- `error`: runtime or Playwright exception.

## Operational Notes
- `pause_for_manual_solve` pauses blocked jobs for manual solve and lets other workers continue.
- CAPTCHA bypass is not attempted; solve challenge manually in the opened browser context.
- Resume routing is automatic:
  - SDE/software/engineering titles -> SDE resume.
  - Analyst/business/operations/compliance/finance titles -> Business resume.
