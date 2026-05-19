---
name: nexus
description: Use when a host or agent workflow needs long-term memory for extracting durable memories, searching prior decisions and preferences, injecting relevant context, maintaining a shared local SQLite memory store, or exporting memory into Obsidian-friendly Markdown files.
---

# Nexus Skill 1.1

Use this skill when the host or agent needs long-term memory with a local SQLite store and optional Obsidian-facing export.

Public workflow:

`setup -> extract -> search -> inject -> feedback -> stats -> maintain -> projection export`

This skill is host-first. Reuse host-provided model backends when available instead of assuming a fixed local model stack.

## When To Trigger

Trigger Nexus when any of the following is true:

1. You need to choose or inspect the SQLite database path used by this skill.
2. You need to choose or inspect the Obsidian vault export path used by this skill.
3. You need to detect whether an existing database or Obsidian export directory already has reusable data.
4. You need to extract durable memory from the current conversation, task context, or document fragments.
5. You need to search prior preferences, decisions, rules, or facts before starting a new task.
6. You need to inject relevant memory into the current task context.
7. You need to accept, ignore, correct, or delete a memory via feedback.
8. You need to inspect current memory state or usage statistics.
9. You need to run memory maintenance.
10. You need to export memories into Obsidian-friendly Markdown files for user reading.

## How Hosts Should Use It

Treat Nexus as a long-term memory skill or plugin, not as a separate primary application.

Minimal host integration:

1. Read this file.
2. Load `config/nexus.json`.
3. On first install or first enablement, confirm:
   - the `db_path`
   - the `obsidian_root_path`
4. Before creating a new library, inspect whether either location already contains data.
5. Call stable entry points only when long-term memory behavior is needed:
   - `src/nexus/skill_entry.py`
   - `adapters/skill_entry.py`

## Configuration Principles

The public configuration should center on these two paths first:

1. `db_path`
2. `obsidian_root_path`

Recommended first-run behavior:

1. Let the user confirm the database location.
2. Let the user confirm the Obsidian export location.
3. If an existing database or existing Obsidian content is detected, ask whether to reuse it.
4. If multiple agents should share memory, point them to the same `db_path`.

If the host already provides model capabilities, Nexus should reuse the host and should not require users to install a fixed local stack such as:

1. Ollama
2. `qwen3:4b`
3. a separate embedding model

## Obsidian Boundary

Current 1.1 Obsidian support is intentionally limited to user-facing export:

1. Export SQLite memory into Obsidian-friendly Markdown.
2. Keep file layout readable inside a vault.
3. Do not promise Markdown writeback from Obsidian in this release.

## Public Capability Surface

The public capability names are:

1. `setup`
2. `extract`
3. `search`
4. `inject`
5. `feedback`
6. `stats`
7. `maintain`
8. `projection export`

If the host needs stable public objects, it may depend on:

1. `MemoryCoprocessor`
2. `Config`
3. `MemoryRecord`
4. `MemoryType`
5. `MemoryStatus`
6. `ScoredMemory`

## What Should Not Be The Main Public Surface

The following should not be treated as the primary Skill 1.1 public surface:

1. `exchange`
2. `host adapter / host runner / event runner`
3. `host events / host contract`
4. `service`
5. host example scripts
6. protocol preacceptance scripts
7. experimental directories such as `lab`
8. legacy module lines such as `anchor / compress / guard / pipeline / ruleforge`
9. Markdown writeback from Obsidian

## Minimal Principle

Interpret Nexus like this:

> Use it when long-term memory is needed.  
> Confirm storage paths early.  
> Reuse existing local data when the user wants shared memory.  
> Keep the public surface focused on local memory and Obsidian-friendly export.
