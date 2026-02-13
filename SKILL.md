---
name: scispace-playwright-search
description: Use Playwright MCP to automate SciSpace Literature Review searches at https://scispace.com/search after authentication is complete in the current browser session. Trigger when the user asks to search SciSpace, export results, apply journal filters, or use journal-slugs.json as default journals.
---

# SciSpace Playwright Search

Authentication precondition (required):
- Before any SciSpace task, confirm the browser session is already logged in.
- If not logged in, stop and ask the user to manually complete login in the same browser session, then continue only after confirmation.

Collect required inputs before browser actions:
- Search query text (paper title, keywords, DOI, or author query).
- Optional explicit journal filter request from user.
- Optional export count (for example top 10).

Default journal behavior:
- If user does not explicitly provide a journal filter, load all journal slugs from `journal-slugs.json` and apply them as default via URL parameter `published_in_journal`.
- Use bundled script:
  - `python build_scispace_search_url.py --query "<query>"`
- Default lookup order for `journal-slugs.json`:
  - `./journal-slugs.json`
  - `~/journal-slugs.json`
  - `~/Desktop/workspace/skills/scispace/journal-slugs.json`
- If no valid file is found, ask user for the file path.

Use this execution sequence:
1. Open a browser tab and navigate to `https://scispace.com/search`.
2. Capture a page snapshot.
3. Verify logged-in state using visible indicators (account avatar/menu, absence of `Log in`/`Sign in` CTA).
4. If not logged in, ask user to manually log in and confirm completion; then re-check logged-in indicators before proceeding.
5. If MFA, CAPTCHA, or email verification appears at any point, pause and ask user to complete it manually, then continue.
6. Determine journal mode:
   - User-provided journal filter: run normal query submission, then apply journal filter in UI.
   - Default journal-slugs mode: generate URL with script and navigate directly to that URL.
7. Ensure tab is `Literature Review > High Quality` (never use `Deep Review` unless user explicitly requests).
8. Wait for results to render and verify filter is active (`Filters (n)` or `published_in_journal` in URL).
9. If user asks for JSON export, always add `Summarized Abstract` column before extraction.
10. If user requests more results, use `Load more papers` until target count is reached.
11. Return results summary or export file details to user.

Interaction rules for Playwright MCP:
- Always call `browser_snapshot` before each major click/fill step and use returned refs.
- Prefer semantic targets (button/input labels and visible text) over brittle selector assumptions.
- Use `browser_wait_for` after navigation, query submit, and filter application.
- If a modal blocks interaction (cookie banner, onboarding), close/dismiss it before continuing.
- If SciSpace redirects during auth/session checks, continue on redirected page and then return to search.

Manual-login handling:
- Do not ask for account credentials.
- Do not automate credential entry.
- If user is not logged in, request manual login completion first.

Export JSON minimum schema (required for every exported paper object):
- `title`
- `authors`
- `journal`
- `publication_date`
- `summarized_abstract`
- `paper_link`
- `doi_url`

Export JSON optional fields:
- `doi`
- `document_type`
- `interaction_count`
- `insights`
- `pdf_status`

Export validation rule (required):
- After JSON generation, verify every paper object contains all minimum schema keys.
- If a value is unavailable, keep the key and use:
  - `""` for string fields
  - `[]` for `authors`
- If `summarized_abstract` is missing for many rows, re-check that `Summarized Abstract` column is visible and regenerate export.

Failure handling:
- If login state cannot be confirmed, report visible blockers and ask user to complete manual login, then resume.
- If journal filter is not found, report available filter labels from snapshot and ask user which one to use.
- If no results remain after filtering, clearly report zero matches.

Output format requirement:
- Include the final query and journal filter used.
- Include login status (`already logged in` or `user completed manual login before run`).
- Provide concise filtered result list (or explicit no-result message).
