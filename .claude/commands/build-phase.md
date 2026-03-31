---
name: build-phase
description: >
  Execute a specific project phase from the CLAUDE.md development plan.
  Use when the user says "build phase X", "execute phase X", "run phase X",
  or "next phase". Reads the phase checklist from CLAUDE.md and executes
  each item using the build-and-verify loop.
---

# Build Phase — Phase-by-Phase Project Executor

Execute one full development phase from the CLAUDE.md plan.

## Workflow

1. **Read CLAUDE.md** to find the specified phase checklist
2. **Read relevant docs/** files for that phase's details
3. **For each checklist item:**
   a. Announce: `"📋 [{phase}] Building: {item}"`
   b. Use the **build-and-verify** skill pattern: write → run → check → fix → repeat
   c. On success: `"✅ [{phase}] Complete: {item}"`
   d. On failure after 10 attempts: `"❌ [{phase}] BLOCKED: {item} — {error}"`
4. **Phase summary** when all items done:
   ```
   ══════════════════════════════════════
   📊 PHASE {N} COMPLETE
   ✅ Passed: X/Y items
   ❌ Blocked: Z items (if any)
   ⏭️  Next: Phase {N+1}
   ══════════════════════════════════════
   ```

## Phase → Docs Mapping

Before starting a phase, READ these reference docs:

| Phase | Must Read Before Starting |
|---|---|
| 0: Foundation | `docs/schema.sql`, `docs/project_spec.md` §9 (requirements), §10 (.env) |
| 1: Data Layer | `docs/odoo_models.md`, `docs/schema.sql` |
| 2: Analytics | `docs/project_spec.md` §4.1–4.8 (module specs) |
| 3: AI Engine | `docs/project_spec.md` §6 (AI architecture), §4.x (prompt templates) |
| 4: Dashboard UI | `docs/project_spec.md` §4.x (module specs for each page) |
| 5: Chat + What-If | `docs/project_spec.md` §4.9 (chat engine) |
| 6: Polish | All docs for review |

## Usage

```
> /build-phase 0

Reading CLAUDE.md... Found Phase 0: Foundation (8 items)
Reading docs/schema.sql for database schema...
Reading docs/project_spec.md §9-10 for requirements and env vars...

📋 [Phase 0] Building: requirements.txt
  [write] Creating requirements.txt with all dependencies...
  [verify] pip install -r requirements.txt --dry-run ✅
✅ [Phase 0] Complete: requirements.txt

📋 [Phase 0] Building: .env.example
  [write] Creating .env.example from project_spec.md §10...
  [verify] File exists and contains all required vars ✅
✅ [Phase 0] Complete: .env.example
...
```

## Critical Rule

NEVER skip the verification step. Every file created must be tested with the
build-and-verify loop before moving to the next checklist item.

If $ARGUMENTS is empty, ask the user which phase to build (0-6).
