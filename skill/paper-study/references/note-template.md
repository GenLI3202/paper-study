# Note file conventions

Read this before writing into a study-note file for the first time in a session.

Everything here exists because study notes have a different failure mode than most documents:
they're written once, read months later, and quoted into work that gets published. They have to
survive being trusted by someone who no longer remembers writing them.

## Contents

- [File skeleton](#file-skeleton) — the structure to create in Phase 0
- [Learning route and progress](#learning-route-and-progress) — one table for priorities and state
- [Citation discipline](#citation-discipline) — what every figure, equation, and number needs
- [Math rendering](#math-rendering) — the chat/file split that trips people up
- [Diagrams](#diagrams) — when and how
- [Foldable annotation branches](#foldable-annotation-branches) — rich tangents without burying the spine
- [Annotation markers](#annotation-markers) — the semantic tags that make notes searchable
- [Synthesis file](#synthesis-file) — for multi-paper reads

---

## File skeleton

```markdown
# <短名> 学习笔记 (<研究焦点> 导向)

> **文献原名**: <full title> (<authors>, <year>, <venue>)
> **定位**: <what's in scope and — just as important — what's deliberately out of scope>
> **相关**: （仅在对应文件存在时添加标准相对 Markdown 链接；单篇精读可省略本行）

## 阅读路线与进度

| 原文章节 | 深度 | Progress | 为什么这样读 |
|---|---|---|---|
| §2.1 问题定义 | 精读 | 已完成 | 决定模型边界 |
| §2.2 不确定性模型 | 最精读 | **进行中**：Eq. 1–3 已领读 | 复现的核心状态方程 |
| §3 实验 | 精读 | 待办 | 建立复现验收指标 |
| §2.3 物理机理 | 跳过 | 已跳过：与当前过滤器关联弱 | 需要时回读 |

- **最后更新**: 2026-08-05

---

## 1. <第一个主题>
...
```

The 定位 line carries the out-of-scope half deliberately. A note that says "电池物理衰减仅作高阶
认知保留" tells a future reader *why* the electrochemistry is thin — without it, thin coverage
reads as an oversight to be fixed rather than a decision that was made.

Number the note's sections by *topic*, and reference the paper's own numbering inside — the note's
organization should serve the reader's mental model, not the paper's table of contents.

## Learning route and progress

Place the agreed route table directly under the metadata so it is the first operational view on
reopening. It serves two jobs that must stay synchronized: **why each section deserves its chosen
depth** and **where the reading currently stands**. Keeping both in one row lets a changed research
filter update priority and state together instead of leaving two trackers to drift apart.

Use four progress states: `已完成` / `进行中` / `待办` / `已跳过：<reason>`. A partially studied
section should say what boundary has been reached — `进行中：Eq. 1–3 已领读` is more restartable
than `当前`. A skipped row remains in the table and carries a reason, because only the reason tells a
future reader whether the skip should be revisited after the filter changes.

Update the relevant cell at every section boundary, not only at session end. Do not create a
second completed/current/pending block elsewhere in the note; duplicate mutable state eventually
contradicts itself.

When migrating an older note that already has both forms, transfer state row by row before deleting
the standalone block: completed → `已完成`; current → `进行中：<exact restart boundary>`; pending →
`待办`; skipped → `已跳过：<reason>`. Preserve the old depth and rationale. If the two trackers
conflict, leave the conflict visible and resolve it from dated evidence or with the reader rather
than silently choosing one.

## Citation discipline

Every figure, equation, table, and specific numeric claim gets a locator precise enough to find
the source page without re-skimming the paper:

```markdown
> **图表出处**: Collath et al., *"Aging aware operation of lithium-ion battery energy storage
> systems: A review"*, Journal of Energy Storage 55 (2022) 105634, Page 4, Fig. 3.
```

Equations get their paper number inline — `(Eq. 3)`, `(Eq. 8)` — so the note can be checked
against the source in seconds.

Named results carry the author who produced them: "Barcellona et al. 用 Peltier 元件主动控温…".
Attribution is exactly what degrades in memory, and exactly what's embarrassing to get wrong in a
citation. Re-read the page before writing an attribution, always.

When a formula is complex and unlikely to be needed verbatim, it's legitimate to record where it
lives instead of transcribing it — "四组拟合公式见原文 Table 2 (p.7)" — and that's *better* than a
transcription you haven't verified character by character.

## Math rendering

Notes and chat may use different renderers, so detect what the current host and target note app
actually support:

- **In the note file**: use LaTeX (`$...$`, `$$...$$`) when the selected Markdown previewer renders
  it. Otherwise use a fenced block with plain symbols and retain the paper's equation number.
- **In chat**: use rendered LaTeX when the host supports it reliably. Otherwise use a fenced code
  block with plain symbols:

  ```
  α_T = γ1 · exp[ -(γ2/R) · (1/T - 1/T_ref) ]      (Eq.5, Arrhenius 温度加速因子)
  ```

When the two renderers differ, the same equation can appear in both forms in one turn — the form
that renders in the message and the form that renders in the file.

### Display math inside quoted foldable annotations

Markdown previewers do not all apply blockquote parsing and math parsing in the same order. In a
quoted `<details>` block, this otherwise-natural source is unsafe:

```markdown
> $$
> x_{t+1}=Ax_t+Bu_t,
> y_t=Cx_t.
> $$
```

Some renderers pass the interior `>` markers to the TeX parser, producing literal `>` symbols,
`>=`, or broken spacing in the rendered equation. Keep each complete display expression on **one
physical source line** instead. Use an `aligned` environment when one display expression needs
multiple visual rows:

```markdown
> $$\begin{aligned} x_{t+1} &= Ax_t+Bu_t, \\ y_t &= Cx_t. \end{aligned}$$
```

"One physical source line" means one Markdown line in the file; soft wrapping in an editor is fine.
`aligned` groups multiple visual rows within one display expression. Multiple independent equations
may each use their own complete one-line display, with quoted blank lines between displays.

Reusable foldable template with math:

```markdown
> <details>
> <summary>💡 扩展讨论：<支线主题></summary>
>
> <说明这部分来自论文、外部背景还是研究推论。>
>
> #### <小标题>
>
> $$\begin{aligned} q_t^{\mathrm{upper}} &= q_{\max}-r_t-m_t, \\ q_t^{\mathrm{lower}} &= q_{\min}+r_t+m_t. \end{aligned}$$
>
> <解释符号、适用条件与来源位置。>
>
> ⚠️ **来源边界**：<说明论文证据与工程推论的边界。>
>
> </details>
```

This pattern satisfies both requirements: every line in the fold remains blockquoted, while no
blockquote marker can be mistaken for part of a multi-line TeX body.

## Diagrams

A diagram earns its place when the content has structure a sentence can't carry: a taxonomy, a
process with branches, an input→mechanism→output chain. It does not earn its place for a list of
independent facts.

Prefer Mermaid when the target host or note app renders it. Otherwise use a labelled plain-text
outline, numbered flow, or another format the reader can inspect; never leave an unrenderable diagram
as the only representation of essential structure. Convert existing ASCII diagrams to Mermaid only
when rendering is available, checking that every box and arrow in the original maps onto a node and
edge in the new one.

Keep one palette across the whole file, so a color means the same thing in every diagram. Pick it
once and reuse via `classDef`:

```
classDef mainNode  fill:#1f77b4,color:#fff,stroke:#0f4c81,stroke-width:2px;   %% 主节点/根
classDef mechanism fill:#e3f2fd,stroke:#1565c0,stroke-width:1.5px;            %% 机制/过程
classDef mitigable fill:#e8f5e9,stroke:#2e7d32,stroke-width:1.5px;            %% 可缓解/可控
classDef condition fill:#f5f0e6,stroke:#8a7550,stroke-width:1.5px;            %% 条件/输入
classDef riskNode  fill:#fde8e8,stroke:#c0392b,stroke-width:1.5px,color:#7f1d1d; %% 风险/不可逆后果
```

Quote any Mermaid node label containing parentheses, colons, or brackets, and use `<br/>` for line
breaks. If the host provides an optional diagram-enhancement capability (for example,
`document-visual-enhancer`), use it for diagram-heavy passes. Otherwise follow the conventions above
and inspect the rendered diagram when rendering or preview tools are available; when they are not,
keep a text equivalent and state that visual rendering was not verified.

## Foldable annotation branches

Keep the paper's argument and the equations or evidence needed to reconstruct it at the agreed
reading depth on the visible main line. Use a foldable
annotation when a valuable branch would otherwise interrupt that line: adjacent theory, an
alternative model family, implementation detail, cited-method background, or a research extension
the reader wants to retain.

Make the entire `<details>` block a Markdown blockquote. Prefix **every line**, including blank
separator lines, with `>`. If the branch contains display equations, also follow the
[single-source-line math pattern](#display-math-inside-quoted-foldable-annotations); do not split a
`$$...$$` expression across several quoted source lines:

```markdown
> <details>
> <summary>💡 扩展讨论：云端 SOC 分析路线</summary>
>
> 这里解释支线，并区分：
>
> - 论文明确陈述的内容；
> - 外部来源提供的背景；
> - 我们面向当前研究作出的推论。
>
> ⚠️ **来源边界**：供应商白皮书的性能数字不是独立同行评审结果。
>
> </details>
```

The quote styling marks the whole branch as commentary; folding preserves a fast path through the
paper's spine. Both are needed — a plain `<details>` hides text but does not visually distinguish
its epistemic role when expanded.

Do **not** fold:

- a formula or definition needed for the next main-line step;
- a data/source boundary required to interpret a visible claim safely;
- a misconception the reader actually demonstrated and will need to see on reread.

A useful fold should still be self-contained and sourced. Folding is not permission to lower
citation discipline or accumulate unrelated background.

## Annotation markers

Consistent markers make notes greppable and let the eye find the high-value parts on a reread.
The set that matters:

| Marker | For | Why it earns a marker |
|---|---|---|
| `⚠️ 核心易错点` | A misconception the reader actually had, with the correction | The highest-value content in the file — no summary would contain it |
| `⚠️ 数据边界` | What the cited experiment covered vs. what's being assumed beyond it | Prevents citing an assumption as a finding |
| `⭐ 研究连接点` | Where this section bears on the reader's own research question | The reason this note exists rather than a PDF highlight |
| `✅ 关键洞察` | A connection drawn across sections or papers | Hard-won, easily lost |
| `💡 扩展讨论` | Valuable tangent that is not part of the paper's core line | Put it in a quoted `<details>` branch so richness does not bury the spine |

Don't apply these mechanically. A file where every paragraph is marked has the same problem as a
file with no markers.

## Synthesis file

For multi-paper reads, alongside the per-paper notes:

```markdown
# <主题> 跨文献综合

> **覆盖文献**: [Paper A](paper-A-notes.md) · [Paper B](paper-B-notes.md) · [Paper C](paper-C-notes.md)
> **研究焦点**: <the filter these papers are being read against>

## 术语对照
| 概念 | Paper A | Paper B | Paper C |
|---|---|---|---|
| 循环深度 | DOC | DOD | ΔDOD |

## 相互印证
- <claim> — A §3.2 与 B §4.1 一致。**注意**: 两者均引用 Ecker 2014 的同一组实验，
  属同源而非独立验证。

## 冲突与分歧
- <topic>: A 主张 <X>（依据…）；B 主张 <Y>（依据…）。差异可能来自 <电芯化学体系/工况范围>。

## 共同盲区
- 三篇均未涉及 <gap> —— 潜在切入点。
```

The term-mapping table looks trivial and isn't: divergent notation for the same construct is the
main source of friction in a multi-paper read, and the table is what makes the other three
sections writable.

Under 相互印证, always check whether agreement is independent. Two papers citing the same
underlying experiment is one data point wearing two hats, and treating it as two is a
straightforward way to overstate confidence in a literature review.
