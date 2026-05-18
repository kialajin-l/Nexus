---
name: nexus
description: Long-term memory skill for agent hosts. Use when the host or workflow needs to extract durable memories from conversations or task context, search prior decisions and preferences, inject relevant memories into the current task, record feedback, inspect memory stats, maintain the store, or export and re-import Markdown memory projections. This skill is host-first: reuse host-provided model backends when available instead of assuming a fixed local model stack.
official: false
version: 1.0.0
---

# Nexus Skill 1.0

Use this skill when the host or agent needs long-term memory.

Public workflow:

`extract -> search -> inject -> feedback -> stats -> maintain -> projection export/import`

This skill is not a standalone Core architecture document and not an installation guide for a fixed local model backend.

## When To Trigger

Trigger Nexus when any of the following is true:

1. You need to extract durable memory from the current conversation, task context, or document fragments.
2. You need to search prior preferences, decisions, rules, or facts before starting a new task.
3. You need to inject relevant memory into the current task context.
4. You need to accept, ignore, correct, or delete a memory via feedback.
5. You need to inspect current memory state or usage statistics.
6. You need to run memory maintenance.
7. You need to export memories into local Markdown files for user review or editing.
8. You need to import user-edited Markdown projections back into the memory store.

## How Hosts Should Use It

Treat Nexus as a long-term memory skill or plugin, not as a separate primary application.

Minimal host integration:

1. Read this file.
2. Load `config/nexus.json`.
3. Call one of the stable entry points when long-term memory is needed:
   - `src/nexus/skill_entry.py`
   - `adapters/skill_entry.py`

## Configuration Principles

The default public configuration should stay minimal:

1. Memory database path
2. Log level

If the host already provides model capabilities, Nexus should reuse the host and should not require users to install a fixed local stack such as:

1. Ollama
2. `qwen3:4b`
3. a separate embedding model

Only when the host does not provide a backend should the integrator attach a local or remote backend explicitly.

## Host Integration Guidance

### Codex-like hosts

1. Put this repository in a discoverable skill or plugin directory.
2. Read `SKILL.md`.
3. Call Nexus entry points only when long-term memory is needed.

### Claude Code-like hosts

1. Mount Nexus as a long-term memory skill.
2. Trigger `extract / search / inject / feedback / stats / maintain / projection` at appropriate workflow points.

### Hermes-like hosts

1. Integrate Nexus as an external long-term memory plugin.
2. Let Hermes decide when to trigger long-term memory behavior.
3. If Hermes already provides model access, reuse it rather than forcing a fixed local model environment.

## Public Capability Surface

The public capability names are:

1. `extract`
2. `search`
3. `inject`
4. `feedback`
5. `stats`
6. `maintain`
7. `projection export`
8. `projection import`

If the host needs stable public objects, it may depend on:

1. `MemoryCoprocessor`
2. `Config`
3. `MemoryRecord`
4. `MemoryType`
5. `MemoryStatus`
6. `ScoredMemory`
7. `ProjectionConfig`
8. `ProjectionMode`
9. `MemoryRiskLevel`

## What Should Not Be The Main Public Surface

The following should not be treated as the primary Skill 1.0 public surface:

1. `exchange`
2. `host adapter / host runner / event runner`
3. `host events / host contract`
4. `service`
5. host example scripts
6. protocol preacceptance scripts
7. experimental directories such as `lab`
8. legacy module lines such as `anchor / compress / guard / pipeline / ruleforge`

Those may remain in the repo as internal or historical material, but they are not the public 1.0 entry story.

## Minimal Principle

Interpret Nexus like this:

> Call it when long-term memory is needed.  
> Do not let it take over the host's main workflow when memory is not needed.  
> It owns memory capability, not the host's entire runtime.
