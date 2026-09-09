# 抽段、对齐、JSON 约定

## 抽段规则（extract_tex.py）

从 `\begin{document}` 扫到 `\end{document}`（没有则全文件）。

**丢弃**

- `%` 行注释（保留 `\%`）
- `\begin{figure}` / `figure*` / `table` / `table*` 整块
- `\bibliography`、`\bibliographystyle`、`\maketitle`、CCS/keyword 块

**切成单位**

| kind | 来源 |
|------|------|
| `sec` | `\section{...}` / `\section*{...}`；摘要记为 `abs` |
| `sub` | `\subsection` / `\subsubsection` |
| `eq` | `equation` / `align` / `displaymath` / `\[...\]` |
| `para` | 其余按空行分段；`\paragraph{X}` 并入该段开头。`\title` / `\author` / CCS 丢弃 |

`id`：`{sec}-{n}`，如 `4-p3`、`5-eq1`。`sec` 字段是章节号或标题 slug。

正文保留 LaTeX 宏（`\cite`、`\ref`、`$...$`、`\begin{itemize}`）。中文 `zh` 也用 `$...$` 和同一套列表宏，不要用 `\\(`，也不要写成 `<ul>`。`build_review.py` 还原多余反斜杠。页面如何收宏见下面「第一版 HTML」。

## 词级 diff（align_diff.py）

Token：

```
\\[a-zA-Z]+(\{[^}]*\})*   # \cite{x}, \emph{y}
\$[^$]+\$
[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*
或单个标点 / 空白（空白并入相邻词）
```

`difflib.SequenceMatcher` 只对齐 token 序列。连续相等 / 插入 / 删除合并成 span。

**不对齐**公式环境内部（整段 `eq` 用等/不等判断，不等则整段 del+ins）。

## review JSON

```json
{
  "title": "MotionDrop",
  "source": "motiondrop.tex",
  "old_ref": "abc123",
  "units": [
    {
      "id": "4-p3",
      "kind": "para",
      "sec": "4",
      "en": "current English (LaTeX)",
      "zh": "中文",
      "old_en": "previous English or null",
      "spans": [
        {"op": "eq", "text": "The "},
        {"op": "del", "text": "old"},
        {"op": "ins", "text": "new"}
      ]
    }
  ]
}
```

无历史时没有 `old_en` / `spans`。`zh` 由 agent 填写。

## 批注 JSON

```json
[
  {
    "id": "c1710-ab12",
    "paraId": "4-p3",
    "side": "en",
    "quote": "selected text",
    "from": 12,
    "to": 80,
    "comment": "批注",
    "createdAt": "2026-09-08T12:00:00"
  }
]
```

`side`：`en` | `zh` | `diff`。HTML 的 localStorage key 为 `lbr-{stem}`，与文件名绑定。`from` / `to` 是该栏可见文本（跳过 KaTeX MathML）上的偏移，可选；没有时按 `quote` 搜索。

## 第一版 HTML

`templates/viewer.html` 就是第一版行为。`build_review.py` 只注入数据，不另写一套页面。写盘后对输出跑 `check_list_html.py`、`check_sel_btn.py`、`check_highlight.py`、`check_margin.py`，失败则退出。

**列表。** `itemize` / `enumerate` 先收成 `<ul class="tex-list">` / `<ol>`，用 `\0L` 占位，再 `esc` 其余文本。Word 审阅先拼接 span 再收同一套宏。`zh` 仍写 `\begin{itemize}`。

**划词按钮。** `#sel-btn` 为 `position:fixed`。`mouseup` 用 `clientX/Y` 经 `placeSelBtn` 贴在松开处并钳进视口。`pairFromSelection` 看 `anchorNode` / `focusNode` / `elementFromPoint`。

**高亮。** 保存时 `quoteFromHit` 记下可见文本与 `from`/`to`。`paintHighlights` 用 `visibleTextNodes`（跳过 `.katex-mathml`）+ `findQuoteOffsets`。优先 `CSS.highlights`；否则 `applyMarkWrap`，公式加 `.hl-math`。`render()` 第一次画完就着色，KaTeX 就绪后再涂一次。

**批注栏。** `.page` 为正文 + 全局 `#margin`。顶栏切换 `notes-hidden` 整栏开关。卡片放在 `#margin-cards`，`top` 相对 `#page` 对齐划选第一行，重叠则向下顺排。

两栏 `minmax(0,1fr)`。`\cite{a,b}` → `[a, b]`，公式交给 KaTeX。
