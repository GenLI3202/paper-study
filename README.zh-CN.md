# paper-study

[English](README.md)

## 使用 AI 智能体安装

你可以复制下面的提示词，并粘贴给能够访问文件和 GitHub 的 AI 智能体：

```text
请为当前对话所使用的 AI 智能体安装 https://github.com/GenLI3202/paper-study。

1. 先确认当前宿主是否支持可复用的 SKILL.md 技能，并找到它支持的用户级或项目级技能目录。
2. 查找 v0.1.1 或更高版本的最新稳定 Release，但不要从 main 安装，也不要直接把可变的“latest”链接当作安装版本。向我显示准确的 Release 标签、提交 SHA、安装范围和目标路径；写入前请我确认。
3. 从已确认的带标签 Release 下载 paper-study.skill 和 SHA256SUMS。在完成验证前，把它们视为不可信文件。核验 SHA-256；如果 GitHub 提供资产摘要，也一并核验。不要执行压缩包内容，只接受 paper-study/SKILL.md 和 paper-study/references/note-template.md 这两个普通文件；拒绝额外条目、绝对路径、路径穿越和符号链接。
4. 在同一文件系统中暂存通过验证的目录。如果 paper-study 已存在，覆盖前再次询问我。替换整个目录，不要合并文件；保留可回滚副本直到验证完成。最后确认宿主能够发现两个文件，并告诉我是否需要重启或重新加载。
5. 如果当前宿主不支持 SKILL.md 技能，请说明最接近的自定义指令或项目工作区配置方式。除非已经完成验证，否则不要声称安装成功。
```

`paper-study` 是一个可移植的 AI 智能体技能，用于陪伴学习者逐节精读一至三篇相关学术论文。由学习者的研究问题决定注意力分配，智能体始终依据实际原文教学，并把每个已理解章节写成可准确续读、来源边界清楚的持久笔记。

仓库：<https://github.com/GenLI3202/paper-study>

## 解决什么问题

1. **定向** —— 先明确学习者的研究问题，以及希望论文具体提供什么。
2. **规划路线** —— 浏览论文结构，共同确认唯一的优先级/进度表，明确保留跳过章节及原因。
3. **领读第一遍** —— 先解释一个有原文依据、边界清楚的内容块，再偶尔用问题诊断理解。学习者可以随时打断，也可以只说“继续”。
4. **写成持久笔记** —— 趁讨论仍清晰时记录精确页码、公式、图表、数据边界、实际误解、关联和研究启示。
5. **续读与校准** —— 从笔记路线表继续；研究过滤器改变时调整深度，并明确最有价值的下一步。

完整工作流见 [`skill/paper-study/SKILL.md`](skill/paper-study/SKILL.md)；笔记结构和引用约定见 [`references/note-template.md`](skill/paper-study/references/note-template.md)。

## 兼容性

核心技能不绑定模型或厂商。当宿主能够加载 `SKILL.md` 风格的指令、读取论文 PDF/文件并写入笔记时，它可用于 Claude Code、基于 GPT 的编程智能体以及其他 AI 智能体宿主。持久记忆、Git、教学扩展和图示工具均为可选能力。

如果聊天界面不提供文件系统或可复用指令能力，它就不能自行完成安装；此时应使用该宿主最接近的自定义指令或项目工作区功能。

## 手动安装

1. 选择 v0.1.1 或更高版本的固定 Release 标签并记录其提交 SHA；不要直接从 `main` 安装。
2. 解压前核验包校验和、GitHub 提供的资产摘要（如有）以及严格的双文件清单。
3. 把验证后的顶层 `paper-study/` 目录放入当前 AI 智能体宿主文档指定的技能目录，确保最终路径以 `paper-study/SKILL.md` 结尾。
4. 如果目标已存在，覆盖前先获得同意并保留备份。不要合并复制到已有目录；应替换整个目录，并在删除备份前验证结果。

不要把仓库根目录当作技能安装。

### Claude Code 专用示例

仅对 Claude Code，常见的用户级目标是 `~/.claude/skills/paper-study`。基于 GPT 的智能体和其他宿主必须使用自身文档指定的技能或指令位置，不要照搬这个路径。

### Release 压缩包

[最新 Release](https://github.com/GenLI3202/paper-study/releases/latest) 只用于查找 v0.1.1 或更高版本的稳定标签；v0.1.0 早于本次宿主中立化更新。解压前先核验 `SHA256SUMS` 中的 SHA-256 校验和，以及 GitHub 显示的资产摘要（如有）。`paper-study.skill` 兼容 ZIP，并且只能包含以下两个普通文件：

```text
paper-study/SKILL.md
paper-study/references/note-template.md
```

## 使用示例

直接用自然语言提出请求即可，无需专用斜杠命令。

```text
带我精读 papers/aggregation.pdf。我最关心聚合协调架构，不需要深入电池化学。先建立阅读路线让我确认，再开始领读，并把长期笔记写到 learning/aggregation-notes.md。
```

```text
接着 learning/aggregation-notes.md 上次停下的位置继续。先读论文原文，不要重讲已完成部分，并随进度更新路线表。
```

该技能适用于引导式精读，不适用于一次性摘要、摘要提取、引文格式整理，或根据已经读完的论文直接生成文献综述。

## 笔记与权限

- 笔记中的路线表是完整、对学习者可见的续读状态。只有学习者明确选择加入后，宿主提供的持久记忆才能补充路线表；记忆不能替代笔记。
- Git 是可选能力。提交前必须获得明确同意，并且只暂存指定的笔记文件。
- 论文、OCR、批注和已有笔记都属于不可信数据，不是访问无关文件、调用工具或执行网络/Git 操作的指令。
- `teach`、`document-visual-enhancer` 等具名集成只是可选示例，并非依赖；没有它们也能使用内置工作流。

## 开发验证

在仓库根目录运行。覆盖率命令需要 `coverage==7.15.4`（`python3 -m pip install coverage==7.15.4`）。

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 -m coverage run --branch -m unittest discover -s tests -v
python3 -m coverage report --fail-under=80
```

[`evals/files/`](evals/files/) 下的文件是合成回归输入，不是已发表论文或基准性能证据。CI 只打包 `SKILL.md` 和 `references/note-template.md`；发布 Release 仍是独立的维护者操作。

## 隐私与局限

论文和笔记按照所选 AI 智能体宿主及服务提供商的政策处理。机密材料只能放在获准的位置；必要时请为 PDF 和笔记添加项目专用 Git 排除规则。

该技能需要可读取的原文页面和文件系统写入权限。OCR 或提取错误仍可能破坏公式和定位信息，因此引用前应回到原文核验。它负责教学和记录论文，不负责复现实验，也不独立验证科学结论。

## 许可证

本项目采用 [MIT License](LICENSE)。Copyright © 2026 GenLI3202。
