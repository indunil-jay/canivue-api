# Domain Docs

How engineering skills consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root: defines the project's canonical domain language.
- **`docs/adr/`**: read Architectural Decision Records touching the area you are about to work in.

If either doesn't exist yet, proceed silently. The `domain-modeling` skill (and `grill-with-docs`) creates them lazily when terms or decisions crystallize.

## File structure

Single-context repo:
```
/
├── GLOSSARY.md
├── docs/adr/
│   ├── 0001-modular-monolith-clean-architecture.md
└── app/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `GLOSSARY.md`. Don't drift to synonyms the glossary explicitly avoids.

## Flag ADR conflicts

If your proposal contradicts an existing ADR in `docs/adr/`, surface it explicitly:
> *Contradicts ADR-NNNN (<decision title>), but worth reopening because...*
