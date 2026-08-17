# paper-study

[简体中文](README.zh-CN.md)

`paper-study` is a Claude skill for studying one to three related academic papers with a learner, section by section. It addresses the gap between a one-shot summary and a durable understanding: the learner's research question determines what deserves attention, Claude teaches from the actual source, and each understood section becomes a restartable note with precise source boundaries.

Repository: <https://github.com/GenLI3202/paper-study>

## What it does

The skill follows one continuous loop:

1. **Orient** — establish the learner's research question and what this paper should contribute to it.
2. **Route and map progress** — survey headings, captions, equations, and the introduction's roadmap; agree on a section-by-section depth/priority table. Its `Progress` column is the note's single source of truth, including explicit skips and their reasons.
3. **Guide the first read** — open the actual pages and explain one bounded chunk before checking understanding. On unread material, explanation comes first and questions are sparse; the learner may interrupt or simply say “continue.” If the learner has already read the chunk or brings an interpretation, targeted questions can diagnose reasoning. The skill never asks the learner to guess unread content and never states formulas, results, or attributions from memory.
4. **Write a durable note** — write each section while the discussion is fresh, using precise page/equation/figure locators, data-boundary warnings, demonstrated misconceptions, cross-links, and research implications. Useful tangents can be folded without hiding the paper's main argument.
5. **Recalibrate and wrap up** — revisit depth at section boundaries when the research filter changes or the paper stops paying off. At the end, synchronize the route table, update available cross-session memory, and state what the paper contributed, where it fell short, and the most useful next step.

The detailed behavior is defined by [`skill/paper-study/SKILL.md`](skill/paper-study/SKILL.md); note structure and citation conventions are in [`references/note-template.md`](skill/paper-study/references/note-template.md).

## Installation

Claude discovers the nested `skill/paper-study` directory; installing the repository root is not sufficient.

### Clone and copy

User-level installation:

```bash
git clone https://github.com/GenLI3202/paper-study.git
mkdir -p "$HOME/.claude/skills"
cp -R paper-study/skill/paper-study "$HOME/.claude/skills/"
```

Project-level installation, run from the target project:

```bash
mkdir -p .claude/skills
cp -R /path/to/paper-study/skill/paper-study .claude/skills/
```

Start a new Claude session after installation so the skill can be discovered.

### Install the v0.1.0 `.skill` archive

The [v0.1.0 release](https://github.com/GenLI3202/paper-study/releases/tag/v0.1.0) provides the package and its checksum. The following user-level installation uses private temporary directories, verifies both the checksum and the exact two-file archive manifest, and replaces an existing installation through a same-filesystem rename with rollback:

```bash
SKILLS_DIR="$HOME/.claude/skills" # For a project install, use: SKILLS_DIR=".claude/skills"
mkdir -p "$SKILLS_DIR"
DOWNLOAD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/paper-study-download.XXXXXX")"
STAGE_DIR="$(mktemp -d "$SKILLS_DIR/.paper-study-install.XXXXXX")"
BACKUP=""
cleanup() {
  rm -rf "$DOWNLOAD_DIR" "$STAGE_DIR"
  if [ -n "$BACKUP" ] && [ -e "$BACKUP" ]; then rm -rf "$BACKUP"; fi
}
trap cleanup EXIT

curl --fail --location \
  https://github.com/GenLI3202/paper-study/releases/download/v0.1.0/paper-study.skill \
  --output "$DOWNLOAD_DIR/paper-study.skill"
curl --fail --location \
  https://github.com/GenLI3202/paper-study/releases/download/v0.1.0/SHA256SUMS \
  --output "$DOWNLOAD_DIR/SHA256SUMS"
( cd "$DOWNLOAD_DIR" && shasum -a 256 -c SHA256SUMS )

EXPECTED_MANIFEST="$(printf '%s\n' \
  'paper-study/SKILL.md' \
  'paper-study/references/note-template.md')"
ACTUAL_MANIFEST="$(unzip -Z1 "$DOWNLOAD_DIR/paper-study.skill" | grep -v '/$' | LC_ALL=C sort)"
if [ "$ACTUAL_MANIFEST" != "$EXPECTED_MANIFEST" ]; then
  printf 'Unexpected package contents; installation stopped.\n' >&2
  exit 1
fi
unzip -q "$DOWNLOAD_DIR/paper-study.skill" -d "$STAGE_DIR"

if [ -e "$SKILLS_DIR/paper-study" ]; then
  BACKUP="$(mktemp -d "$SKILLS_DIR/.paper-study-backup.XXXXXX")"
  rmdir "$BACKUP"
  mv "$SKILLS_DIR/paper-study" "$BACKUP"
fi
if ! mv "$STAGE_DIR/paper-study" "$SKILLS_DIR/paper-study"; then
  if [ -n "$BACKUP" ]; then mv "$BACKUP" "$SKILLS_DIR/paper-study"; fi
  exit 1
fi
if [ -n "$BACKUP" ]; then rm -rf "$BACKUP"; BACKUP=""; fi
```

## Invocation examples

Ask naturally; no special slash command is required.

English:

```text
Help me study papers/aggregation.pdf section by section. I care about coordination architecture, not battery chemistry. Build a reading route for my approval before teaching, and keep durable notes in learning/aggregation-notes.md.
```

```text
Continue where we stopped in learning/aggregation-notes.md. Read the paper's actual pages, do not reteach completed sections, and update the route table as we go.
```

Chinese:

```text
带我精读 papers/aggregation.pdf。我最关心聚合协调架构，不需要深入电池化学。先建立阅读路线让我确认，再开始领读，并把长期笔记写到 learning/aggregation-notes.md。
```

```text
接着 learning/aggregation-notes.md 上次停下的位置继续。先读论文原文，不要重讲已完成部分，并随进度更新路线表。
```

The skill is intended for guided deep reading, not one-shot summarization, abstract extraction, citation formatting, or generating a literature review from papers already read.

## Notes, memory, and Git

- **Notes are durable state.** The route table records current progress; the body records source-grounded understanding. Multiple papers receive separate note files plus a synthesis file.
- **Memory is resumable context.** When the host provides persistent memory, the skill records the current research filter, progress, and next step. Memory complements rather than replaces the reader-visible note, and availability depends on the Claude environment.
- **Git is optional and consent-based.** If notes are inside a Git repository, the skill asks once whether it may commit each completed section and follows that answer. It must not commit without explicit consent. When allowed, it follows the repository's conventions and stages only named note files, never the whole working tree.

## Optional integrations

The skill works standalone with file/PDF reading and filesystem write tools.

- [`teach`](https://github.com/anthropics/skills) can add tutoring techniques, while the skill's own explanation-first loop remains sufficient.
- `document-visual-enhancer` can add fuller Mermaid guidance and validation for diagram-heavy notes; the bundled note conventions include a standalone diagram path.

Neither integration is required.

## Repository layout

```text
.
├── README.md
├── README.zh-CN.md
├── LICENSE
├── .gitignore
├── skill/
│   └── paper-study/
│       ├── SKILL.md
│       └── references/
│           └── note-template.md
├── evals/
│   ├── evals.json
│   └── files/
│       ├── aggregation-paper.md
│       ├── aging-paper.md
│       ├── admm-background.md
│       └── legacy-study-notes.md
├── scripts/
│   └── validate.py
└── tests/
    └── test_validate.py
```

## Validation, evals, coverage, and packaging

Run the local checks from the repository root:

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 -m coverage run --branch -m unittest discover -s tests -v
python3 -m coverage report --fail-under=80
```

Install the `coverage` package first if it is not already available. The repository validator checks the skill metadata and allowlisted package contents, local Markdown links, eval schema and fixture paths, privacy exclusions, and standalone/optional-dependency wording. The test suite exercises success and failure paths; branch-aware coverage must remain at least 80%.

The six cases in [`evals/evals.json`](evals/evals.json) cover orientation before teaching, explanation-first multi-turn reading, legacy-note migration, multi-paper synthesis, source-labelled foldable tangents, and targeted questioning of an already-read section. Run them through the official `skill-creator` evaluation workflow for behavioral regression testing. The files under `evals/files/` are deliberately synthetic examples/regression inputs; they are not published papers, a public benchmark dataset, or evidence of benchmark performance. Passing local tests or the coverage gate is not a published behavioral benchmark score.

For official structural validation and packaging, use the `skill-creator` scripts from its directory (in a Python environment with PyYAML available):

```bash
REPO_ROOT="/absolute/path/to/paper-study"
python -m scripts.quick_validate "$REPO_ROOT/skill/paper-study"
python -m scripts.package_skill "$REPO_ROOT/skill/paper-study" "$REPO_ROOT/dist"
unzip -l "$REPO_ROOT/dist/paper-study.skill"
```

`package_skill` validates before creating `dist/paper-study.skill`; the archive is ZIP-compatible and contains the top-level `paper-study/` skill directory.

## Privacy

The skill contains no standalone uploader, but papers and notes read by Claude are processed according to the policies of the Claude environment in which it runs. Keep confidential material in approved locations.

[`.gitignore`](.gitignore) excludes generated evaluation workspaces, `dist/`, `*.skill`, coverage output, Python caches, and `.DS_Store`. It does **not** exclude arbitrary PDFs or study-note paths. Add project-specific exclusions or keep sensitive sources and notes outside this repository before running evals or Git commands.

## Limitations

- Best suited to one to three related papers; broader literature reviews need a different workflow.
- Requires readable source pages and filesystem write access. OCR or PDF extraction errors can still corrupt equations and locators, so verify notes against the source before citing them.
- It teaches and documents papers; it does not reproduce experiments or validate scientific claims independently.
- Persistent memory, Git, and optional integrations depend on the host environment. Git commits always require explicit consent.

## License

Released under the [MIT License](LICENSE). Copyright © 2026 GenLI3202.
