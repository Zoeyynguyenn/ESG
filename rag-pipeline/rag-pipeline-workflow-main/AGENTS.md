# RAG Pipeline Workflow

This repository stores file-backed workflow state for long-running RAG learning, research, implementation, and reporting sessions.

Core rule: do not rely only on chat history. Before substantial work, read the active workflow files and continue from disk state.

## Language

All documentation artifacts must be written in Vietnamese.

Keep technical identifiers in English when appropriate: tool names, file paths, package names, API names, metrics, model names, and command names.

## Active State

Read these files first when starting, resuming, or re-orienting:

1. `.rag/current_plan`
2. `.rag/<plan-id>/plan.md`
3. `.rag/<plan-id>/progress.md`
4. `.rag/<plan-id>/findings.md`
5. `.rag/<plan-id>/decisions.md`
6. `.rag/<plan-id>/experiment_log.md`
7. `.rag/<plan-id>/eval_set.md`

If `.rag/current_plan` is missing, ask before creating a new plan.

## Workflow Intents

| Intent | Action |
|---|---|
| `/rag status` or status request | Show current goal, version, phase, blockers, and next step |
| `/rag plan` or planning request | Update `plan.md` and confirm the next version/phase |
| `/rag research` | Write findings to `findings.md` and decisions to `decisions.md` if a choice is made |
| `/rag experiment` | Define experiment config, run/record result in `experiment_log.md` |
| `/rag eval` | Update or run `eval_set.md`, then summarize metrics |
| `/rag report` | Update `daily_report.md` or create a report artifact |
| `/rag compact` | Flush current state to files before context reset/long chat continuation |

## Required Operating Rules

1. Update `progress.md` after every meaningful work block.
2. Write research/tool notes into `findings.md`.
3. Record technical decisions immediately in `decisions.md` with rationale.
4. Record every experiment in `experiment_log.md`, even failed ones.
5. Keep `eval_set.md` as the stable evaluation source across versions.
6. Do not move to the next version until exit criteria for the current version are met or the user explicitly approves skipping.
7. End each work session by updating `daily_report.md`.
8. When chat becomes long, run the compact checklist in `progress.md` and persist state.

## RAG Version Roadmap

The default roadmap has six versions:

1. Version 1: Mini RAG Baseline
2. Version 2: Evaluated Evidence RAG
3. Version 3: Improved Evidence Retrieval
4. Version 4: Structured Extraction RAG
5. Version 5: Workflow / Product-Oriented RAG
6. Version 6: Advanced RAG

Each version must produce:

1. Implementation artifact or experiment artifact.
2. Evaluation notes.
3. Report summary.
4. Decision on whether to continue, improve, or advance.
