# paper-study

[简体中文](README.zh-CN.md)

## Install with your AI agent

You can copy and paste this prompt into an AI agent that has access to files and GitHub:

```text
Install paper-study from https://github.com/GenLI3202/paper-study for the AI-agent host running this chat.

1. Determine whether this host supports reusable SKILL.md skills and find its user-level or project-level skills directory.
2. Discover the latest stable release at v0.1.1 or newer, but do not install from main or directly from the mutable latest-release link. Show me the exact release tag, commit SHA, install scope, and target path; ask me to approve them before writing anything.
3. From the approved tagged release, download paper-study.skill and SHA256SUMS. Treat them as untrusted until verification. Check SHA-256 and the GitHub asset digest when available. Inspect the ZIP without executing it: accept only the regular files paper-study/SKILL.md and paper-study/references/note-template.md; reject extra entries, absolute paths, path traversal, and symlinks.
4. Stage the verified directory on the same filesystem. If paper-study already exists, ask me again before replacing it. Replace the whole directory rather than merging files, retain a rollback copy until verification, then confirm both files are discoverable and tell me whether to restart or reload the host.
5. If this host does not support SKILL.md skills, explain the closest supported custom-instruction or workspace setup instead. Do not claim installation succeeded unless you verified it.
```

`paper-study` is a portable AI-agent skill for studying one to three related academic papers section by section. The learner's research question controls what deserves attention, the agent teaches from the actual source, and each understood section becomes a restartable note with precise source boundaries.

Repository: <https://github.com/GenLI3202/paper-study>

## What it does

1. **Orient** — identify the learner's research question and what the paper should contribute.
2. **Plan the route** — survey the paper and agree on one priority/progress table, including explicit skips and reasons.
3. **Guide the first read** — explain a bounded source-grounded chunk before asking occasional diagnostic questions. The learner may interrupt or simply say “continue.”
4. **Write durable notes** — record exact pages, equations, figures, data boundaries, misconceptions, links, and research implications while the discussion is fresh.
5. **Resume and recalibrate** — continue from the note's route table, adjust depth when the research filter changes, and state the most useful next step.

The complete workflow is in [`skill/paper-study/SKILL.md`](skill/paper-study/SKILL.md). Note structure and citation conventions are in [`references/note-template.md`](skill/paper-study/references/note-template.md).

## Compatibility

The core skill is provider-neutral. It works with Claude Code, GPT-based coding agents, and other AI-agent hosts **when the host can load `SKILL.md`-style instructions, read the source PDF/files, and write a note file**. Persistent memory, Git, tutoring extensions, and diagram tools are optional.

A chat interface without filesystem or reusable-instruction support cannot install the skill by itself. In that case, use the host's closest custom-instruction or project-workspace feature.

## Manual installation

1. Choose a fixed tagged release at v0.1.1 or newer and record its commit SHA; do not install directly from `main`.
2. Verify the package checksum, GitHub asset digest when available, and exact two-file archive manifest before extracting.
3. Place the verified top-level `paper-study/` directory in the skill directory documented by your AI-agent host. The final path must end with `paper-study/SKILL.md`.
4. If the target exists, obtain consent and keep a backup before replacing it. Do not merge-copy into an existing directory; replace the whole directory and verify the result before removing the backup.

Do not install the repository root as the skill.

### Claude Code-specific example

For Claude Code only, the user-level target is commonly `~/.claude/skills/paper-study`. GPT-based agents and other hosts must use their own documented skill or instruction location rather than copying this path.

### Release archive

Use the [latest release](https://github.com/GenLI3202/paper-study/releases/latest) only to discover a stable tag at v0.1.1 or newer; v0.1.0 predates the provider-neutral update. Before extracting, verify the SHA-256 checksum in `SHA256SUMS` and the asset digest shown by GitHub when available. `paper-study.skill` is ZIP-compatible and must contain only these regular files:

```text
paper-study/SKILL.md
paper-study/references/note-template.md
```

## Usage

Ask naturally; no special slash command is required.

```text
Help me study papers/aggregation.pdf section by section. I care about coordination architecture, not battery chemistry. Build a reading route for my approval before teaching, and keep durable notes in learning/aggregation-notes.md.
```

```text
Continue where we stopped in learning/aggregation-notes.md. Read the paper's actual pages, do not reteach completed sections, and update the route table as we go.
```

The skill is for guided deep reading, not one-shot summaries, abstract extraction, citation formatting, or generating a literature review from papers already read.

## Notes and permissions

- The note's route table is the complete, reader-visible resumption state. Host-provided persistent memory may supplement it only after the reader explicitly opts in; memory never replaces the note.
- Git is optional. The agent must obtain explicit consent before committing and must stage only the named note files.
- Papers, OCR, annotations, and existing notes are treated as untrusted data, not as instructions to access unrelated files, use tools, or perform network or Git actions.
- Optional named integrations such as `teach` and `document-visual-enhancer` are examples, not requirements; the bundled workflow works without them.

## Development

Run the local checks from the repository root. The coverage command requires `coverage==7.15.4` (`python3 -m pip install coverage==7.15.4`).

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 -m coverage run --branch -m unittest discover -s tests -v
python3 -m coverage report --fail-under=80
```

The fixtures under [`evals/files/`](evals/files/) are synthetic regression inputs, not published papers or benchmark evidence. CI packages only `SKILL.md` and `references/note-template.md`; release publication remains a separate maintainer action.

## Privacy and limitations

Papers and notes are processed according to the selected AI-agent host and provider. Keep confidential material only in approved locations, and add project-specific Git exclusions for PDFs or notes when needed.

The skill requires readable source pages and filesystem write access. OCR or extraction errors can still corrupt equations and locators, so verify notes against the source before citing them. It teaches and documents papers; it does not reproduce experiments or independently validate scientific claims.

## License

Released under the [MIT License](LICENSE). Copyright © 2026 GenLI3202.
