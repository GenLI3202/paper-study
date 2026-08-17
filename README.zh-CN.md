# paper-study

[English](README.md)

`paper-study` 是一个 Claude 技能，用于陪伴学习者逐节精读一至三篇相关学术论文。它解决“一次性摘要”与“真正形成可长期复用的理解”之间的缺口：由学习者的研究问题决定注意力分配，Claude 始终依据实际原文教学，并把每个已理解章节写成可准确续读的持久笔记。

仓库：<https://github.com/GenLI3202/paper-study>

## 解决什么问题

该技能执行一个连续闭环：

1. **定向（Orient）** —— 先明确学习者的研究问题，以及希望这篇论文具体提供什么。
2. **规划路线并映射进度** —— 浏览章节标题、图表说明、公式和引言中的路线说明；共同确认逐节阅读深度与优先级表。表格的 `Progress` 列是笔记内唯一的进度事实来源，明确保留跳过章节及其原因。
3. **领读第一遍** —— 打开实际原文页面，先解释一个边界清楚的内容块，再检查理解。面对未读材料，默认先解释、少提问；学习者可以随时打断，也可以只说“继续”。如果学习者已经读过当前内容或带来了具体解释，则可用针对性问题诊断其推理。技能不会要求学习者猜测未读内容，也不会凭记忆陈述公式、结果或归属。
4. **写成持久笔记** —— 趁讨论仍清晰时逐节写入笔记，记录精确页码/公式/图表定位、数据边界、学习者实际出现的误解、跨章节链接和研究启示。支线内容可以折叠，但不能遮蔽论文主线。
5. **重新校准并收尾** —— 在章节边界重新检查阅读深度；当研究过滤器改变或论文不再有价值时及时调整。结束时同步路线表、更新环境所支持的跨会话记忆，并明确论文带来了什么、缺少什么以及最有价值的下一步。

完整行为由 [`skill/paper-study/SKILL.md`](skill/paper-study/SKILL.md) 定义；笔记结构和引用约定见 [`references/note-template.md`](skill/paper-study/references/note-template.md)。

## 安装

Claude 需要发现嵌套的 `skill/paper-study` 目录；只安装仓库根目录并不够。

### 克隆并复制

用户级安装：

```bash
git clone https://github.com/GenLI3202/paper-study.git
mkdir -p "$HOME/.claude/skills"
cp -R paper-study/skill/paper-study "$HOME/.claude/skills/"
```

项目级安装（在目标项目中运行）：

```bash
mkdir -p .claude/skills
cp -R /path/to/paper-study/skill/paper-study .claude/skills/
```

安装后请启动新的 Claude 会话，让环境重新发现该技能。

### 安装 v0.1.0 `.skill` 压缩包

[v0.1.0 Release](https://github.com/GenLI3202/paper-study/releases/tag/v0.1.0) 提供技能包及其校验和。以下用户级安装使用私有临时目录，校验 SHA-256 与严格的双文件归档清单，并通过同一文件系统内的重命名替换已有版本；失败时会回滚：

```bash
SKILLS_DIR="$HOME/.claude/skills" # 若安装到项目，请使用：SKILLS_DIR=".claude/skills"
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

## 调用示例

直接用自然语言提出请求即可，无需专用斜杠命令。

英文：

```text
Help me study papers/aggregation.pdf section by section. I care about coordination architecture, not battery chemistry. Build a reading route for my approval before teaching, and keep durable notes in learning/aggregation-notes.md.
```

```text
Continue where we stopped in learning/aggregation-notes.md. Read the paper's actual pages, do not reteach completed sections, and update the route table as we go.
```

中文：

```text
带我精读 papers/aggregation.pdf。我最关心聚合协调架构，不需要深入电池化学。先建立阅读路线让我确认，再开始领读，并把长期笔记写到 learning/aggregation-notes.md。
```

```text
接着 learning/aggregation-notes.md 上次停下的位置继续。先读论文原文，不要重讲已完成部分，并随进度更新路线表。
```

该技能适用于引导式精读，不适用于一次性摘要、摘要提取、引文格式整理，或根据已经读完的论文直接生成文献综述。

## 笔记、记忆与 Git

- **笔记是持久状态。** 路线表记录当前进度，正文记录有原文依据的理解。多篇论文各自使用独立笔记，并另建一个综合文件。
- **记忆用于跨会话续读。** 当运行环境支持持久记忆时，技能会记录当前研究过滤器、进度和下一步。记忆只补充而不替代学习者可见的笔记，其可用性取决于 Claude 运行环境。
- **Git 可选且以同意为前提。** 如果笔记位于 Git 仓库中，技能会询问一次是否可以在每节完成后提交，并在后续遵守该选择。未经明确同意不得提交。获得同意后，应遵循现有仓库约定，只暂存明确指定的笔记文件，绝不暂存整个工作树。

## 可选集成

只要具备文件/PDF 读取和文件系统写入工具，该技能即可独立工作。

- [`teach`](https://github.com/anthropics/skills) 可补充教学技巧；即使没有它，技能内置的“先解释”循环也足够运行。
- `document-visual-enhancer` 可为图示较多的笔记补充更完整的 Mermaid 指南和验证；内置笔记约定已经提供独立可用的图示方案。

两项集成都不是必需依赖。

## 仓库结构

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

## 本地验证、评测、覆盖率与打包

在仓库根目录运行本地检查：

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 -m coverage run --branch -m unittest discover -s tests -v
python3 -m coverage report --fail-under=80
```

如果当前环境尚未提供 `coverage` 包，请先安装。仓库验证器会检查技能元数据与打包内容白名单、本地 Markdown 链接、评测结构与输入路径、隐私排除项，以及独立运行/可选依赖措辞。测试套件覆盖成功和失败路径；分支感知覆盖率必须保持至少 80%。

[`evals/evals.json`](evals/evals.json) 中的六个用例覆盖：教学前定向、“先解释”的多轮领读、旧笔记进度迁移、多论文综合、标明来源的可折叠支线，以及针对已读章节的聚焦提问。行为回归测试应通过官方 `skill-creator` 评测流程运行。`evals/files/` 下的文件是有意构造的合成示例/回归输入；它们不是已发表论文、公开基准数据集，也不能作为基准性能证据。通过本地测试或覆盖率门槛不等于发布了行为基准分数。

官方结构验证和打包请在 `skill-creator` 目录中使用其脚本（Python 环境需已安装 PyYAML）：

```bash
REPO_ROOT="/absolute/path/to/paper-study"
python -m scripts.quick_validate "$REPO_ROOT/skill/paper-study"
python -m scripts.package_skill "$REPO_ROOT/skill/paper-study" "$REPO_ROOT/dist"
unzip -l "$REPO_ROOT/dist/paper-study.skill"
```

`package_skill` 会先验证，再创建 `dist/paper-study.skill`；该文件兼容 ZIP 格式，内部包含顶层 `paper-study/` 技能目录。

## 隐私

该技能本身不包含独立上传器，但交给 Claude 读取的论文和笔记会按照当前 Claude 运行环境的政策处理。请仅在获准的位置存放机密材料。

[`.gitignore`](.gitignore) 排除了生成的评测工作区、`dist/`、`*.skill`、覆盖率输出、Python 缓存和 `.DS_Store`，但**不会**排除任意 PDF 或学习笔记路径。在运行评测或 Git 命令前，请增加项目专用排除规则，或把敏感来源和笔记放在本仓库之外。

## 局限

- 最适合一至三篇相关论文；范围更大的文献综述需要其他工作流。
- 需要可读取的原文页面和文件系统写入权限。OCR 或 PDF 提取错误仍可能破坏公式和定位信息，引用前应回到原文核验。
- 它负责教学和记录论文，不负责复现实验，也不独立验证科学结论。
- 持久记忆、Git 和可选集成都取决于宿主环境；Git 提交始终需要明确同意。

## 许可证

本项目采用 [MIT License](LICENSE)。Copyright © 2026 GenLI3202。
