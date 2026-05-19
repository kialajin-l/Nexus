<div align="center">
  <img src="assets/readme/nexus-banner.svg" alt="Nexus banner" width="100%" />
</div>

> This is a Vibe Coding project: Built with AI, for AI-augmented development.

![License](https://img.shields.io/badge/License-MIT-F2C94C)
![Version](https://img.shields.io/badge/Version-v1.1.0-2D9CDB)
![Python](https://img.shields.io/badge/Python-%3E%3D3.10-27AE60)

**English** | [中文](README.md)

## What Nexus Is

`Nexus Skill / Plugin 1.1` is a long-term memory skill for agent hosts.

This release focuses on two upgrades:

1. exporting to Obsidian-friendly Markdown
2. configuring the database path and Obsidian path first, with existing-data detection

## Installation

Pick the command for your host and run it in the terminal:

### Claude Code

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh claude-code
```

### Codex

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh codex
```

### Hermes

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh hermes
```

### OpenClaw

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh openclaw
```

### DeepSeek TUI

```bash
git clone https://github.com/kialajin-l/Nexus.git && cd Nexus && ./install.sh deepseek
```

If the one-line command does not work, you can still install manually:

1. clone the repository
2. enter the repository directory
3. run `./install.sh <host>`

After installation, check and edit:

- `db_path`
- `obsidian_root_path`

The default config file lives in the installed skill directory:

- `config/nexus.json`

## What To Do First

After installation, confirm:

1. where the SQLite database should live
2. where the Obsidian export directory should live
3. whether either location already contains data worth reusing

If the host supports command invocation, start with:

```bash
nexus setup --db-path "<db-path>" --obsidian-root "<vault-path>"
```

This saves the paths to `config/nexus.json` and helps detect:

- whether the database file already exists
- whether the Obsidian directory already exists
- whether reusable content is already present

## Usage Guide

These are the user-facing feature names and typical usage patterns.

### 1. Install and initialize

Use this when the user wants to:

- install Nexus
- enable it for the first time
- set the database path
- set the Obsidian path
- check whether previous data can be reused

Typical phrases:

- configure Nexus
- set the database path
- set the Obsidian path
- check whether an existing memory library already exists
- reuse the old database

### 2. Save information

Use this when the user wants to:

- save a preference
- save a decision
- save a rule
- turn the current conversation into long-term memory

Typical phrases:

- remember this preference
- save this decision
- store this rule
- extract long-term memory from this conversation

### 3. Find past memory

Use this when the user wants to:

- check what was decided before
- search past preferences
- find related decisions
- find prior rules or facts

Typical phrases:

- check what I said before
- search earlier database decisions
- find previous preferences
- look for related memory

### 4. Bring past memory into the current task

Use this when the user wants to:

- answer with past preferences in mind
- reuse earlier decisions in a new task
- enrich the current task with historical context

Typical phrases:

- use previous rules first
- bring relevant memory into this task
- add prior decisions to the current context

### 5. Correct or remove memory

Use this when the user wants to:

- mark a memory as wrong
- ignore a memory
- correct a memory
- delete a memory

Typical phrases:

- this memory is wrong
- ignore this one
- correct this memory
- delete this memory

### 6. Check memory library status

Use this when the user wants to:

- see how many memories exist
- inspect memory status
- check library size

Typical phrases:

- show current memory status
- count current memories
- inspect long-term memory health

### 7. Maintain the memory library

Use this when the user wants to:

- run maintenance
- reduce long-term noise
- keep the memory library healthy

Typical phrases:

- clean up the memory library
- run memory maintenance
- organize long-term memory

### 8. Export to Obsidian

Use this when the user wants to:

- export Markdown into Obsidian
- turn memory into a note library
- generate a readable long-term memory directory

Typical phrases:

- export to Obsidian
- export memory as Markdown
- generate memory files for Obsidian

Command example:

```bash
nexus -p my-project projection export \
  --db-path "<db-path>" \
  --output "<vault-root>" \
  --group-by topic \
  --obsidian-friendly
```

## Prompt Guide

The best prompts are normal feature requests rather than internal module names.

Recommended examples:

- configure Nexus
- set the database path
- set the Obsidian path
- check whether there is an existing memory library
- remember this preference
- save this decision
- check what I said before
- bring relevant memory into this task
- this memory is wrong
- show current memory status
- organize the memory library
- export to Obsidian

## Local Multi-Agent Usage

Nexus 1.1 supports multiple local agents sharing one long-term memory base, but this is not automatic.

To share memory:

1. multiple hosts must use the same `db_path`
2. if they should share the same exported notes, they should also use the same `obsidian_root_path`
3. they should run compatible Nexus versions and schema

Recommended setup:

1. choose one shared database path
   for example `D:\\shared\\nexus\\nexus.db`
2. point Hermes, Codex, Claude Code, and other hosts to that same `db_path`
3. if needed, point them to the same `obsidian_root_path` too

The intended model is:

- private local libraries by default
- explicit shared memory when users choose the same database path

## What 1.1 Adds

This release mainly adds:

1. Obsidian-friendly export
2. first-run storage path setup
3. detection of existing database and export directories
4. clearer local multi-agent sharing guidance

## What Is Not Included

The following are not part of the current 1.1 primary public surface:

- Obsidian writeback as a supported promise
- `exchange`
- `host adapter / host runner / event runner`
- `host events / host contract`
- `service`
- host example scripts
- `tests`
- `lab`

## License

MIT
