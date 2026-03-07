---
name: scispace-playwright-search
description: Use Playwright MCP to automate SciSpace Literature Review searches at https://scispace.com/search after authentication is complete in the current browser session. Trigger when the user asks to search SciSpace, export results, apply journal filters, or use journal-slugs.json as default journals.
---

# SciSpace Playwright Search

## Playwright MCP CDP Setup (required first-time setup)

SciSpace uses CloudFront WAF which blocks headless Chromium browsers (403 error).
The Playwright MCP **must** connect to the user's real Chrome browser via Chrome DevTools Protocol (CDP).

### Step 1: Verify or configure Playwright MCP with CDP

Check if Playwright MCP is already configured with `--cdp-endpoint`:
```bash
claude mcp get playwright 2>&1
```

If NOT configured with CDP, run:
```bash
claude mcp remove playwright 2>&1
claude mcp add playwright -- npx @playwright/mcp@latest --cdp-endpoint http://localhost:9222
```

Important: Do NOT modify the plugin marketplace `.mcp.json` file directly — it will be ignored by the plugin cache system. Use `claude mcp add` to register MCP servers in the local project config.

### Changing the CDP endpoint

To change the CDP endpoint (e.g. different port), edit `~/.claude.json` directly:

Navigate to:
```
projects > <your-project-path> > mcpServers > playwright > args
```

Change the endpoint value in the `args` array:
```json
"args": [
  "@playwright/mcp@latest",
  "--cdp-endpoint",
  "http://localhost:<new-port>"
]
```

No need to `claude mcp remove/add` — just edit the file and restart Claude Code.

### Step 2: Launch Chrome with remote debugging

The user must launch Chrome with `--remote-debugging-port` on the machine whose browser will be controlled. All existing Chrome processes must be closed first, otherwise the flag is silently ignored.

```bash
# Close all Chrome processes first
pkill -f chrome

# Launch with remote debugging
# --remote-debugging-address=0.0.0.0 allows connections from other machines (required for remote/SSH scenarios)
# --user-data-dir uses a separate profile to avoid conflicts with existing Chrome sessions
google-chrome \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --user-data-dir=/tmp/chrome-debug-profile
```

- **Local machine**: Claude Code and Chrome on the same machine → endpoint is `http://localhost:9222`
- **Remote machine**: Chrome runs on a different machine (e.g. accessed via SSH) → endpoint is `http://<chrome-machine-ip>:9222`

### Step 3: Verify CDP is listening

```bash
curl -s http://localhost:9222/json/version
```

Should return JSON with `Browser`, `webSocketDebuggerUrl` etc. If empty or connection refused, Chrome was not launched correctly (likely existing Chrome processes were still running).

### Step 4: Restart Claude Code

After configuring MCP and launching Chrome, the user must restart Claude Code (`/exit` then re-launch) for the new MCP config to take effect.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 403 ERROR from CloudFront | Playwright using its own headless Chromium | Must use CDP connection to real Chrome |
| CDP port not listening | Existing Chrome processes prevent `--remote-debugging-port` | `pkill -f chrome` first, then relaunch |
| Human Verification / CAPTCHA | SciSpace bot detection | Use CDP with real Chrome; user completes CAPTCHA manually |
| MCP config not applied after edit | Plugin cache doesn't pick up `.mcp.json` changes | Use `claude mcp add` instead; restart Claude Code |
| `about:blank` with no user tabs | CDP not connected; Playwright launched its own browser | Verify `curl localhost:9222/json/version` works before restarting Claude Code |

---

## Authentication precondition (required)

- Before any SciSpace task, confirm the browser session is already logged in.
- After CDP connection, navigate to `https://scispace.com/search` and capture a snapshot.
- Verify logged-in state using visible indicators (account avatar/menu with user name, "My Library" link, absence of `Sign up`/`Log in` CTA).
- If not logged in, ask user to manually log in in the same Chrome browser, then refresh and re-check.

## Collect required inputs before browser actions

- Search query text (paper title, keywords, DOI, or author query).
- Optional explicit journal filter request from user.
- Optional export count (for example top 10).

## Default journal behavior

- **Always** use `journal-slugs.json` as the default journal filter, unless the user explicitly requests otherwise (e.g. no filter, or a specific journal).
- Load all journal slugs from `journal-slugs.json` and apply them via URL parameter `published_in_journal`.
- Use bundled script to generate the search URL with journal filters:
  - `python build_scispace_search_url.py --query "<query>"`
- Default lookup order for `journal-slugs.json`:
  - `<skill-base-dir>/journal-slugs.json` (bundled with this skill)
  - `./journal-slugs.json`
  - `~/journal-slugs.json`
- If no valid file is found, ask user for the file path.
- The `journal-slugs.json` contains 78 curated SSCI journals covering finance, economics, accounting, and management domains.

## Execution sequence

1. Verify CDP connection is active (`curl -s http://localhost:9222/json/version`).
2. Navigate to `https://scispace.com/search` and capture a page snapshot.
3. Verify logged-in state (see authentication precondition above).
4. If not logged in, ask user to manually log in and confirm completion; then re-check.
5. If MFA, CAPTCHA, or email verification appears at any point, pause and ask user to complete it manually, then continue.
6. Determine journal mode:
   - User-provided journal filter: run normal query submission, then apply journal filter in UI.
   - Default journal-slugs mode: generate URL with script and navigate directly to that URL.
7. Ensure tab is `Literature Review > High Quality` (never use `Deep Review` unless user explicitly requests).
8. Wait for results to render and verify filter is active (`Filters (n)` or `published_in_journal` in URL).
9. If user asks for JSON export, always add `Summarized Abstract` column before extraction.
10. If user requests more results, use `Load more papers` until target count is reached.
11. Return results summary or export file details to user.

## Interaction rules for Playwright MCP

- Always call `browser_snapshot` before each major click/fill step and use returned refs.
- Prefer semantic targets (button/input labels and visible text) over brittle selector assumptions.
- Use `browser_wait_for` after navigation, query submit, and filter application.
- If a modal blocks interaction (cookie banner, onboarding), close/dismiss it before continuing.
- If SciSpace redirects during auth/session checks, continue on redirected page and then return to search.
- When snapshot output is too large, save to a file with `browser_snapshot(filename=...)` and read the relevant sections.

## Manual-login handling

- Do not ask for account credentials.
- Do not automate credential entry.
- If user is not logged in, request manual login completion first.

## Export JSON minimum schema (required for every exported paper object)

- `title`
- `authors`
- `journal`
- `publication_date`
- `summarized_abstract`
- `paper_link`
- `doi_url`

## Export JSON optional fields

- `doi`
- `document_type`
- `interaction_count`
- `insights`
- `pdf_status`

## Export validation rule (required)

- After JSON generation, verify every paper object contains all minimum schema keys.
- If a value is unavailable, keep the key and use:
  - `""` for string fields
  - `[]` for `authors`
- If `summarized_abstract` is missing for many rows, re-check that `Summarized Abstract` column is visible and regenerate export.

## Failure handling

- If login state cannot be confirmed, report visible blockers and ask user to complete manual login, then resume.
- If journal filter is not found, report available filter labels from snapshot and ask user which one to use.
- If no results remain after filtering, clearly report zero matches.
- If 403 error from CloudFront, check CDP setup (see troubleshooting table above).

## Output format requirement

- Include the final query and journal filter used.
- Include login status (`already logged in` or `user completed manual login before run`).
- Provide concise filtered result list (or explicit no-result message).
