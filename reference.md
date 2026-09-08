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

正文保留 LaTeX 宏（`\cite`、`\ref`、`$...$`）。中文 `zh` 也用 `$...$`，不要用 `\\(`。`build_review.py` 还原多余反斜杠；`viewer.html` 再把 `\cite{a,b}` → `[a, b]`、`itemize` → 列表、`\%` → `%`，公式交给 KaTeX。两栏 `minmax(0,1fr)`，长宏可断行。

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
    "comment": "批注",
    "createdAt": "2026-09-08T12:00:00"
  }
]
```

`side`：`en` | `zh` | `diff`。HTML 的 localStorage key 为 `lbr-{stem}`，与文件名绑定。
