# Issue Tracker: GitHub

Issues and specs for this repository live as GitHub issues on [indunil-jay/canivue-api](https://github.com/indunil-jay/canivue-api). Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc or file for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

The repository is inferred from git remote: `https://github.com/indunil-jay/canivue-api.git`.

## Pull Requests as a Triage Surface

**PRs as a request surface: no.** (Only issues are triaged by default).

## When a skill says "publish to the issue tracker"

Create a GitHub issue using `gh issue create`.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

## Wayfinding Operations

Used by the `wayfinder` skill (`.agents/skills/wayfinder/SKILL.md`). The **map** is a single issue with **child** issues as decision tickets.

- **Map**: A single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. Run `gh issue create --label wayfinder:map`.
- **Child ticket**: An issue linked to the map as a sub-issue or referenced in a task list with `Part of #<map>` at the top of the body. Labels: `wayfinder:<type>` (`research` / `prototype` / `grilling` / `task`).
- **Blocking**: Declared using GitHub dependency edges or `Blocked by: #<n>, #<n>` at the top of the child ticket body.
- **Frontier query**: List open children where all blocking tickets are closed.
- **Claim**: Assign to current agent/dev.
- **Resolve**: Comment resolution, close ticket, and append gist + link to map's Decisions-so-far.
