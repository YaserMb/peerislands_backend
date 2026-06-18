---
name: update-docs
description: Update this project's documentation after meaningful backend, schema, test, or workflow changes. Use when changes should be reflected in backend/AGENTS.md, backend/REPO_MAP.md, backend/PRD.md, README.md, AI_USAGE.md, or related setup documentation.
metadata:
  author: PeerIslandTest
  version: 1.0.0
  category: documentation
---

# Update Docs

After completing a feature, architectural change, migration, endpoint, or test
workflow change, update the relevant documentation. Keep docs concise and
specific to this order-processing backend.

## Scope

Update only documentation that is directly affected by the change.

| File | Purpose |
|------|---------|
| `backend/AGENTS.md` | Agent workflow rules, verification commands, implementation conventions. |
| `backend/REPO_MAP.md` | Current and planned file paths, ownership, task-to-file index. |
| `backend/PRD.md` | Product requirements and acceptance criteria. Update only when requirements change. |
| `backend/README.md` | Human setup/run/test/migration instructions once created. |
| `backend/AI_USAGE.md` | AI-assisted development notes once created. |
| `backend/.env.example` | Required environment variables once created. |

Do not update unrelated markdown files or add broad historical notes unless the
user explicitly asks for that.

## Step 1: Identify What Changed

Classify the change before editing docs.

| Change type | Docs to check |
|-------------|---------------|
| New or modified endpoint | `backend/REPO_MAP.md`, `backend/README.md` if setup/API usage changed |
| New API module/router | `backend/REPO_MAP.md`, `backend/AGENTS.md` if routing conventions changed |
| New DB model or migration | `backend/REPO_MAP.md`, `backend/README.md` migration instructions |
| New dependency | `backend/README.md`, `backend/REPO_MAP.md` if it introduces a new layer/tool |
| New env variable | `backend/.env.example`, `backend/README.md` |
| Auth/security behavior change | `backend/PRD.md` if requirement changed, otherwise `backend/REPO_MAP.md` |
| Order lifecycle/business rule change | `backend/PRD.md`, `backend/REPO_MAP.md` |
| Test workflow change | `backend/AGENTS.md`, `backend/README.md` |
| New project-local skill | `backend/AGENTS.md`, `backend/REPO_MAP.md` |

Skip doc updates for tiny formatting changes, typo fixes, or implementation
details that do not affect future development.

## Step 2: Read Exact Files

Read only the docs selected in Step 1. Prefer direct file reads over broad
searches. If a file does not exist yet, create it only when the change makes it
useful now.

## Step 3: Update By Responsibility

- `AGENTS.md` answers: what should future agents do?
- `REPO_MAP.md` answers: where is code located and where should new work go?
- `PRD.md` answers: what behavior is required?
- `README.md` answers: how does a human set up, run, migrate, and test?
- `AI_USAGE.md` answers: how was AI used and what was manually verified?
- `.env.example` answers: what configuration is needed?

Avoid duplicating the same explanation across files. Link or summarize when a
second file needs awareness.

## Step 4: Verify

After editing docs:

1. Re-read the changed sections.
2. Confirm file paths mentioned in docs exist or are clearly marked as planned.
3. Confirm commands are realistic for the current project state.
4. Keep `backend/AGENTS.md` under roughly 120 lines and `backend/REPO_MAP.md`
   under roughly 300 lines.

## Notes For This Repo

- `backend/PRD.md` is currently the source of truth for intended behavior.
- The implementation is still scaffold-level, so distinguish current files from
  planned files.
- Use `Decimal`/server-side calculations for money-related docs and examples.
- Keep customer ownership, admin-only reporting, and status-transition rules
  visible in docs when order behavior changes.
