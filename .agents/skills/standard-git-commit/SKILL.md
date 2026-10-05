---
name: standard-git-commit
description: Guidelines and rules for authoring git commits in Canivue API using Conventional Commits. Use whenever creating git commits, drafting commit messages, or reviewing commit history.
---

# Conventional Git Commit Standards

This repository adheres to the **Conventional Commits** specification. Every commit message must be clean, informative, and follow the established project history style.

---

## Commit Message Format

```
<type>(<scope>): <short imperative subject>

<detailed body explaining WHY and WHAT changed>
- Bullet points covering specific technical modifications
- Explicit rationale for non-obvious design decisions

[optional footer: Closes #123, Refs #456]
```

---

## Allowed Types

- `feat`: A new user-facing feature or API endpoint
- `fix`: A bug fix
- `chore`: Maintenance tasks, dependencies, scaffolding, git config
- `docs`: Documentation updates, README changes, docstrings
- `test`: Adding or modifying tests, test harness, test fixtures
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `style`: Formatting, missing semicolons, whitespace (no code behavior change)

---

## Standard Scopes

Common scopes used in `canivue-api`:
- `core`: Database sessions, config, exception handling, base response envelope
- `shared`: BaseEntity, BaseRepositoryProtocol
- `ml`: Machine learning training pipeline, datasets, evaluation, metrics, model registry
- `vision`: Vision diagnosis feature module or model
- `behavioural`: Sensor/behavioural analysis feature module or model
- `nlp`: Symptom extraction NLP feature module or model
- `sample`: The blueprint sample feature
- `<feature_name>`: Specific business feature (e.g. `dogs`, `assessments`, `users`)

---

## Rules

1. **Imperative Mood**: Use imperative present tense in the subject ("add feature", "fix issue", NOT "added" or "adds").
2. **Lowercase**: Subject line starts with lowercase and has no trailing period.
3. **Contextual Body**: For any non-trivial change, provide a multi-line explanation of *why* the change was made and key architectural details.
