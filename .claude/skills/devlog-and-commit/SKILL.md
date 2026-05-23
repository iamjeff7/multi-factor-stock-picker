---
name: devlog-and-commit
description: >
  Log a dev session to DEVLOG.md, then stage, commit, pull, and push. Use this skill
  whenever the user says "log and commit", "wrap up the session", "finish the task",
  "end of session", "log my work", "commit and push", or any similar phrase indicating
  they're done working and want to record what happened and ship the code. Trigger even
  if the user only mentions one part (e.g. "just log it" or "just commit") — run the
  relevant step and ask about the other.
---

# Devlog and Commit Skill

Two steps, always in this order:
1. **LOG** — append a structured entry to `DEVLOG.md`
2. **COMMIT** — stage, commit, pull (resolving conflicts), push

---

## Trigger Phrases

"log and commit", "wrap up", "finish the task", "end of session", "log my work",
"commit and push", "ship it", "done for today"

---

## Step 1 — LOG to DEVLOG.md

### Gather context

Before writing the entry, collect:

1. **Today's date/time** — run `date '+%Y-%m-%d %H:%M:%S'`
2. **Session number** — read the last entry in `DEVLOG.md` and increment by 1.
   If `DEVLOG.md` doesn't exist, session number is 1.
3. **Files changed** — run `git diff --name-only HEAD` (staged + unstaged).
   Also include any untracked files: `git ls-files --others --exclude-standard`
4. **Completed tasks** — read `.claude/session.md` for tasks marked done this session.

---

### Entry format

```markdown
## Session N — YYYY-MM-DD HH:MM:SS

- Goal: <what we set out to do>

- What I Built:
  - `path/to/file.py` — <one line description>
  - `path/to/other.md` — <one line description>

- Decisions Made:
  - <non-obvious choice> — <why>
  - <non-obvious choice> — <why>

- What Didn't Work:
  - <bug, abandoned approach, or surprise>

- Tasks Completed:
  - <task name from tasks.md>
```

### Formatting rules (strictly enforced)

- Session title is `## Session N — YYYY-MM-DD HH:MM:SS`
- Every section label is a top-level bullet (`- Goal:`, `- What I Built:`, etc.)
- Multi-item sections use nested bullets (`  - item`) — never flatten to plain lines
- Single-item sections may be inline: `- Goal: <text>`
- Blank line between each major section
- If a section has nothing to report, write `- <Section>: none` — never omit a section

### Append to file

Use a bash command to append — never rewrite the whole file:

```bash
cat >> DEVLOG.md << 'EOF'

## Session N — YYYY-MM-DD HH:MM:SS
...
EOF
```

Confirm to the user:
> "Session N logged to DEVLOG.md."

---

## Step 2 — COMMIT and PUSH

Run these steps in order. Stop and report if any step fails.

### Stage
```bash
git add -A
git status
```
Show the user a short summary of what's staged.

### Commit
Write a descriptive commit message based on the session log. Format:
```
<imperative summary under 72 chars>

- <file or change 1>
- <file or change 2>
- <file or change 3>
```
Example:
```
Add VIX risk-off filter signal and unit tests

- src/signals/macro/vix_filter.py — new macro signal
- tests/test_vix_filter.py — unit tests for all branches
- .claude/tasks.md — marked Task 2 complete
```

Run:
```bash
git commit -m "<message>"
```

### Pull with rebase
```bash
git pull --rebase origin <current-branch>
```

If rebase conflicts occur:
1. Show the user which files conflict
2. For each conflicted file, show the conflict markers and ask which version to keep
   (or whether to merge them manually)
3. After the user decides: `git add <resolved-file>` then `git rebase --continue`
4. If the user wants to abort: `git rebase --abort`

### Push
```bash
git push origin <current-branch>
```

Confirm to the user:
> "Pushed to `<branch>`. Session N is wrapped up."

---

## Error Handling

| Problem | Action |
|---|---|
| `DEVLOG.md` doesn't exist | Create it with a `# DEVLOG` heading, then append first entry |
| `.claude/tasks.md` missing | Skip Next Session / Tasks Completed, note it in the entry |
| `git push` rejected (non-conflict) | Show the error, ask the user how to proceed — do not force push |
| Rebase conflict | Walk through file by file, never auto-resolve |
| Nothing staged (`git status` clean) | Tell the user, ask if they still want to log — skip commit/push |

---

## Full Flow Summary

```
user: "log and commit"
        ↓
run: date, git diff, read tasks.md + session.md
        ↓
ask: one-question session summary
        ↓
write entry → append to DEVLOG.md → confirm
        ↓
git add -A → show staged files
        ↓
git commit -m "<descriptive message>"
        ↓
git pull --rebase → resolve conflicts if any
        ↓
git push → confirm done
```