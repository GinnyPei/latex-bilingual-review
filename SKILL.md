---
name: latex-bilingual-review
description: >-
  Generates a bilingual Chinese-English HTML review of a LaTeX paper, with
  Word-style track-changes diffs against a git or file history, plus selectable
  comments that persist via localStorage and JSON export. Use when the user
  asks for 中英对照, 全文对照, 历史版本对比, Word 审阅, track changes,
  bilingual review, paragraph-by-paragraph translation of a .tex paper, or
  commentable review HTML.
---

# LaTeX 中英对照 + Word 式审阅

把 `.tex` 做成可划词批注的 HTML：逐段中英对照，并可对历史版本做 **Word 审阅粒度**（词级增删线）对比。批注写入 localStorage，并导出 JSON 以便入库。

## 何时用

- 「生成全文中英对照」「第四五章对照」
- 「和上一版 / 某个 commit 对比，要 Word 审阅那种」
- 「对照页要能 comment 并保存」

不要用这个 skill 去改论文正文；它只产出审阅页。改稿走 `paper-revision-workflow`。

## 输出位置

默认写到论文仓库的 `review/`：

```
review/
  <stem>_bilingual.html      # 打开这个
  <stem>_review.json         # 段落 + 译文 + diff
  <stem>_comments.json       # 批注存档（导出/导入）
  vendor/katex/              # 公式（若已有则复用）
```

`<stem>` 默认是主 tex 文件名（如 `motiondrop`）。

## 工作流

复制并勾选：

```
- [ ] 1 定位主 .tex，确认范围（全文 / 指定 \section）
- [ ] 2 抽段：scripts/extract_tex.py
- [ ] 3 若要比历史：再抽旧版，scripts/align_diff.py
- [ ] 4 为每个正文单位写中文（agent 翻译，不调用机翻 API）
- [ ] 5 scripts/build_review.py 生成 HTML
- [ ] 6 打开 HTML，说明批注如何保存
```

### 1 定范围

- 主文件：用户指定，否则仓库里的主 `*.tex`（有 `\documentclass` 的那个）。
- 范围：`all`（默认）或章节号，如 `4,5`、`abs,4,5`（`abs` / `abstract` = 摘要）。
- 历史对比（可选）：`git show <rev>:<path>`，或用户给的旧 `.tex`。未指定 rev 时问一句；常用 `HEAD`、`HEAD~1`、某个 hash。

### 2 抽段

在论文仓库根目录执行（把 `SKILL_DIR` 换成本 skill 的绝对路径）：

```bash
python3 "$SKILL_DIR/scripts/extract_tex.py" motiondrop.tex \
  --sections 4,5 \
  --out review/motiondrop_current.json
```

全文去掉 `--sections`。从 git 抽旧版：

```bash
python3 "$SKILL_DIR/scripts/extract_tex.py" motiondrop.tex \
  --git abc123 \
  --out review/motiondrop_old.json
```

规则见 [reference.md](reference.md)。不要手写抽段；脚本漏了再补丁脚本。

### 3 Word 式对齐 + 词级 diff

只要用户要历史对比就跑：

```bash
python3 "$SKILL_DIR/scripts/align_diff.py" \
  review/motiondrop_old.json \
  review/motiondrop_current.json \
  --out review/motiondrop_review.json
```

粒度必须接近 Word 审阅：

- 先按章节标题对齐，再对剩余段落做相似度匹配。
- 对齐后的英文做 **词级** `SequenceMatcher`（LaTeX 命令如 `\cite{...}` 当作一个词）。
- 展示：删除 = 红 + 删除线；插入 = 绿 + 下划线；未改为原文。
- 整段只在旧版 = 整段删除；只在新版 = 整段插入。

### 4 写中文

对 `review.json` / `current.json` 里每个 `kind` 为 `para`、`eq`、`sec`、`sub` 的单位补 `zh`：

- 学术书面语，术语与正文一致（change energy、prefill、KV cache 等可保留英文）。
- 公式左右两栏保持同一 TeX，不要翻译符号。行内公式写成 `$...$`（与抽段英文一致），不要写 `\\(` / `\\)`；`json.dumps` 会自己转义，再手写一层会显示成 `\\(\alpha\\)`。
- 标题也写中文（`zh` 字段）。
- 把译文写回 JSON，不要另起一份手写 HTML。
- 全文可按章节分批写回同一 JSON；未译的 `zh` 留空，页面显示「（待译）」。

### 5 生成 HTML

```bash
python3 "$SKILL_DIR/scripts/build_review.py" \
  review/motiondrop_review.json \
  --title "MotionDrop 审阅" \
  --out review/motiondrop_bilingual.html \
  --comments review/motiondrop_comments.json
```

无历史 diff 时把 `current.json`（已含 `zh`）传给 `build_review.py`。

`build_review.py` 会把 sidecar 里已有批注嵌进 HTML（本机无 localStorage 时作为初始值），并在 `review/vendor/katex/` 缺失时从本 skill 的 `vendor/katex` 复制。

### 6 告诉用户怎么批注

- 浏览器打开生成的 HTML（路径用 file:// 即可）。
- 布局：左侧正文（中英对照），**右侧固定批注分栏**，互不遮挡；「显示 / 隐藏批注栏」收起右侧栏。窄屏时批注栏改到正文下方。
- 划选任一侧文字 →「添加批注」。
- 批注只写入浏览器 localStorage，**不会**自动改仓库里的 `review/<stem>_comments.json`（file:// 页面没有写盘权限）。
- 「导出批注到文件」下载 JSON，再手动覆盖 `review/<stem>_comments.json` 才能入库。
- 「导入 JSON」从该文件恢复。

## 硬规则

- 不把批注写进 `.tex`。
- 不编造旧版没有的句子来「对齐」。
- 译文忠实，不借翻译改技术含义。
- 中文公式分隔符与英文相同：`$...$`、`\[...\]`。禁止在 JSON 的 `zh` 里写 `\\(`。生成交给 `build_review.py`（它会把残留的 `\\(` 还原并改成 `$`）。
- 页面负责把 `\cite` / `\ref` / `\emph` / `itemize` 等收成可读标记；两栏用 `minmax(0,1fr)` 等宽，避免长 citation 撑破中文栏。
- 对照页不是论文编译产物；改稿仍以 `.tex` 为准。

## 附加文件

- 对用户怎么说、产物是什么：[examples.md](examples.md)
- 抽段 / diff / JSON 约定：[reference.md](reference.md)
- 页面行为：[templates/viewer.html](templates/viewer.html)
