---
name: grillme
description: A relentless interview to sharpen a plan, decision, or design. Use when the user asks to "grill me", "grillme", or stress-test their ideas before implementation.
---

# Grillme

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

> Note: Also available as `grill-me` (`.agents/skills/grill-me/SKILL.md`) and `grilling` (`.agents/skills/grilling/SKILL.md`).

## The Process

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

### Formatting Rounds

Format a round like so:

```markdown
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

### Navigating the Tree

- Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them.
- Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.
- **Finding facts is your job, never the user's.** When a frontier question needs a fact from the environment (filesystem, codebase, tools, configs), dispatch a subagent or inspect the files directly; don't ask the user for anything you could look up yourself. Don't block on it: an open exploration is an unsettled prerequisite, so only downstream questions wait; ask the rest of the frontier now.
- The _decisions_ are the user's: put each to them clearly and wait for their choice.
- The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
