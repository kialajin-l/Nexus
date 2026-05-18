<div align="center">
  <img src="assets/readme/nexus-banner.svg" alt="Nexus banner" width="100%" />
</div>

> 🧠 This is a Vibe Coding project: Built with AI, for AI-augmented development.

![License](https://img.shields.io/badge/License-MIT-F2C94C)
![Version](https://img.shields.io/badge/Version-v1.0.0-2D9CDB)
![Python](https://img.shields.io/badge/Python-%3E%3D3.10-27AE60)

**English** | [中文](README.md)

## What Nexus Is

`Nexus Skill / Plugin 1.0` is a public long-term memory entry point for external users and agents.

Its purpose is straightforward: turn useful context from ongoing work into searchable, injectable, feedback-driven memory instead of leaving everything trapped inside one-off conversations.

The public workflow is:

`extract -> store -> retrieve -> inject -> feedback -> maintain`

## Core Capabilities

<div align="center">
  <img src="assets/readme/memory-flow.svg" alt="Nexus memory flow" width="100%" />
</div>

Nexus 1.0 focuses on six public capabilities:

1. `extract`
   Pull durable memories out of conversations, task context, and document fragments.
2. `retrieve / search`
   Find relevant memories when a new task begins.
3. `inject`
   Turn the best matches into context that can be fed back into an agent workflow.
4. `feedback`
   Accept, ignore, correct, or delete memories based on real usage.
5. `stats`
   Inspect memory volume and state.
6. `maintain`
   Keep the memory base healthy over time instead of letting it decay into noise.

<div align="center">
  <img src="assets/readme/capability-cards.svg" alt="Nexus capability overview" width="100%" />
</div>

## Where It Fits

- Long-running development work that should not re-explain the same project context every turn
- Agent collaboration where preferences, decisions, and rules should persist
- Toolchains that want reusable memory across later tasks
- Local-first memory workflows without turning the public entry point into a large host platform

## Quick Start

### 1. Install As A Skill

The public purpose of this repository is an Agent Skill / Plugin, not a standalone runtime showcase.

Keep these files as the primary public surface:

- `SKILL.md`
- `config/nexus.json`
- `src/nexus/`
- `adapters/`

If your host loads skills through a Python environment, install dependencies first:

```bash
pip install -e .[ollama]
```

or:

```bash
pip install -e .[openai]
```

### 2. Configure The Skill

Edit [config/nexus.json](E:/code/Nexus/config/nexus.json):

```json
{
  "db_path": "data/nexus.db",
  "llm_provider": "ollama",
  "llm_model": "qwen3:4b",
  "llm_base_url": "http://localhost:11434",
  "llm_api_key": "",
  "embedding_model": "nomic-embed-text",
  "embedding_dimension": 768,
  "log_level": "INFO"
}
```

This config defines how the skill connects to memory storage, the LLM backend, and embeddings inside the host environment.

### 3. Let The Host Read The Skill Entry

Hosts should primarily read:

- [SKILL.md](E:/code/Nexus/SKILL.md)

Nexus should be consumed as a long-term memory skill, not presented primarily as a standalone CLI product.

The public skill capabilities are:

- `extract`
- `search`
- `inject`
- `feedback`
- `stats`
- `maintain`

### 4. Integrate Into The Host

For hosts that support discoverable Skill / Plugin directories, the recommended shape is:

1. Place this repository inside the host's Skill / Plugin search path
2. Let the host read `SKILL.md`
3. Let the host call Nexus only when long-term memory operations are needed

The current unified integration entry points are:

- `src/nexus/skill_entry.py`
- `adapters/skill_entry.py`

That keeps Nexus positioned as a memory capability plugin rather than exposing low-level implementation details.

### 5. Current Host Framing

Given the current 1.0 public surface:

- For Codex-like hosts: read `SKILL.md`, then call the Nexus skill entry when memory is needed
- For Claude Code-like hosts: mount Nexus as a long-term memory skill in the workflow
- For Hermes-like hosts: integrate Nexus as an external memory plugin and let the host decide when to trigger extraction, retrieval, and injection

If the docs expand further, they should prioritize host integration guidance rather than low-level runtime usage.

## Repository Layout

```text
Nexus/
├── README.md
├── README.en.md
├── SKILL.md
├── config/
│   └── nexus.json
├── assets/
│   └── readme/
├── src/
│   └── nexus/
├── adapters/
└── tests/
```

## Current Boundaries

This README is intentionally scoped to `Nexus Skill / Plugin 1.0` as a public memory interface. It does not expand into lower-level internal design.

The focus of 1.0 is simple: make long-term memory understandable, installable, and usable through one clear public entry point.

What is not part of the primary 1.0 public surface:

- host event integration
- service-oriented deployment shape
- cross-environment interoperability details
- experimental research and archive material

## Toward 2.0

Future `2.0` work can expand the public surface, but this README keeps it intentionally high level:

- broader host integration
- more flexible cross-environment memory collaboration
- more stable long-running memory workflows
- clearer plugin-style installation and integration

## License

MIT
