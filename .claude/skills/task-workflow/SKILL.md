---
name: task-workflow
description: >
  Lightweight multi-session task management for Claude Code. Use this skill whenever the
  user says "create a plan", "set up tasks", "let's plan this out", "continue" (to resume
  work), or asks Claude to track a list of tasks across sessions. Maintains three files in
  .claude/: tasks.md (checklist), requirements.md (specs + verification steps), and
  session.md (current task + progress + context). Handles the full loop: plan → work →
  verify → commit → next task. Trigger this skill any time the user wants structured,
  resumable, multi-step work tracked in files.
---

# Task Workflow Skill

Manages multi-session work using three files in `.claude/`:
- `tasks.md` — numbered checklist
- `requirements.md` — specs per task + global verification steps
- `session.md` — current task, progress, context

---

## Trigger Words

| Phrase | Action |
|---|---|
| "create a plan" / "set up tasks" / "let's plan" | → Run **SETUP** flow |
| "continue" | → Run **State Machine** from CHECK_STATUS |

---

## SETUP Flow

When the user says "create a plan", run this interview then create all three files.

**Step 1 — Ask for tasks:**
> "What are the tasks you want to complete? List them one by one, or describe the overall
> goal and I'll break it down."

**Step 2 — Ask for requirements and verification:**
> "For each task, what are the acceptance criteria? And what are your global verification
> steps — e.g. `npm test`, `pytest`, lint checks, build commands?"

**Step 3 — Create the three files:**

### `.claude/tasks.md`
```markdown
- [ ] Task 1: <name>
- [ ] Task 2: <name>
- [ ] Task 3: <name>
```

### `.claude/requirements.md`
```markdown
## Global Guidelines
- <any cross-cutting rules the user mentioned>

## Verification & Definition of Done
- <verification command 1>
- <verification command 2>

## Task 1: <name>
- <requirement>
- <requirement>

## Task 2: <name>
- <requirement>
- <requirement>
```

### `.claude/session.md`
```markdown
**Current Task:** Task 1

## What's Done
(nothing yet)

## Next Steps
1. <first step for Task 1>

## Context
(none yet)
```

After creating the files, tell the user:
> "Plan created. Say **continue** to start working."

---

## State Machine

Activated on "continue". Follow this exactly.

```
user: "continue"
       ↓
CHECK_STATUS — Read session.md
       |
       ├─ Status = "Complete" ──→ AWAITING_COMMIT
       │                            Ask permission, STOP
       │                            user: yes ──→ MARK_TASK_COMPLETE
       │
       └─ Status = "in progress" ──→ WORKING
```

### State: CHECK_STATUS
1. Read `.claude/session.md`
2. If session.md has `Status: Complete` → go to **AWAITING_COMMIT**
3. Otherwise → go to **WORKING**

---

### State: WORKING
1. Read `.claude/requirements.md` to get specs for the current task
2. Read `.claude/tasks.md` to confirm which task is active
3. Do the work for the current task
4. Update `.claude/session.md` with progress:

```markdown
**Current Task:** Task N: <name>
Status: in progress

## What's Done
- <completed step>

## Next Steps
1. <remaining step>

## Context
- <any relevant discoveries, edge cases, decisions>
```

5. When the task implementation is complete → go to **VERIFY**

---

### State: VERIFY
Run every step listed under `## Verification & Definition of Done` in `requirements.md`.

- All pass → go to **COMPLETE**
- Any fail → return to **WORKING**, fix the issue, re-verify

---

### State: COMPLETE
Write to `.claude/session.md`:

```markdown
**Current Task:** Task N: <name>
Status: Complete

## What's Done
- <all completed steps>
- All verification checks passed

## Next Steps
1. Commit changes

## Context
- <discoveries, decisions>
```

Then STOP and tell the user:
> "Task N complete and all checks pass. Say **continue** to commit and move to the next task."

---

### State: AWAITING_COMMIT
Tell the user:
> "Ready to commit Task N. Shall I commit and move to Task N+1?"

Wait for user: **yes** → go to **MARK_TASK_COMPLETE**

---

### State: MARK_TASK_COMPLETE
1. In `.claude/tasks.md`, mark the current task complete: `- [x] Task N: <name>`
2. Check if there are remaining `- [ ]` tasks:
   - **Yes — more tasks remain:** Update `.claude/session.md` to point to the next task:
     ```markdown
     **Current Task:** Task N+1: <name>
     Status: in progress

     ## What's Done
     - Task 1 ... Task N complete

     ## Next Steps
     1. <first step for Task N+1>

     ## Context
     - <carry forward any relevant context>
     ```
     Tell the user: "Task N committed. Moving to Task N+1. Say **continue** to keep going."
   - **No more tasks:** Tell the user: "All tasks complete! 🎉"
3. Once done all the tasks, use log and commit skill to log to DEVLOG.md, commit and push

---

## File Format Reference

### `tasks.md`
```markdown
- [ ] Task 1: Extract UserService
- [x] Task 2: Add tests
- [ ] Task 3: Update documentation
```

### `requirements.md`
```markdown
## Global Guidelines
- No breaking changes to public APIs
- Add logging for error cases
- Follow existing code style

## Verification & Definition of Done
- npm test — all tests pass
- npm run lint — no errors
- npm run build — successful

## Task 1: Extract UserService
- Move user methods from AppService to new UserService
- Maintain backward compatibility
- Update dependency injection

## Task 2: Add tests
- Cover happy path and error cases
- Include null/undefined edge cases
- Mock external dependencies
```

### `session.md`
```markdown
**Current Task:** Task 3

## What's Done
- Extracted UserService (commit abc123)
- Added tests (commit def456)

## Next Steps
1. Update documentation

## Context
- Using npm for package management
- Found edge case: user.email can be null
```

---

## Rules

- Never skip the VERIFY state — always run the verification commands before marking complete
- Never move to the next task without user confirmation at AWAITING_COMMIT
- Always write session.md after every state transition so progress survives a session end
- If `.claude/session.md` doesn't exist when "continue" is said, tell the user to run "create a plan" first
- Keep Context in session.md lean — only what's needed to resume work cold