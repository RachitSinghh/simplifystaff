<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

## Before coding
- Run Ponytail before writing or editing any code, including small fixes.
- If Ponytail is unavailable or fails, stop and tell me instead of continuing without it.

## Code style
- Write no comments of any kind: no inline comments, block comments, docstrings, or TODOs.
- Do not remove comments from existing code unless I ask.
- Make code self-explanatory through clear names and small functions.

## Git
- Never commit, push, or amend without my explicit permission. Ask first, every time.
- Do not add a Co-Authored-By line or any mention of Claude in commit messages.
- Before starting a bug fix, new feature, or integration, create a new branch from the current one. Never work directly on main.
- Name branches by type and purpose, for example `fix/login-redirect` or `feat/stripe-integration`.

## After finishing
- Summarize in 3-4 short bullet points, one line each.
- Cover what changed, which files were touched, and anything I need to act on.
- Skip step-by-step recaps, restating my request, and closing offers.

<!-- END:nextjs-agent-rules -->

## Ticket workflow
- Working through `documents/TICKETS.md`: the moment a ticket's acceptance criteria are all verified, say so explicitly (e.g. "FOUND-2 done") before doing anything else.
- Then move straight on to the next ticket per the dependency graph, without waiting for a go-ahead — unless something's genuinely ambiguous and needs a decision only I can make.
