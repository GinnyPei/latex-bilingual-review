# latex-bilingual-review

Cursor Agent Skill：把 `.tex` 做成可划词批注的 HTML（中英对照 + Word 式词级审阅）。

批注存在浏览器 `localStorage`，导出 JSON 后才能入库。生成对照页需要仓库里的 `.tex`；换对比版本必须重新跑脚本，HTML 里不能现场选 git commit。

第一版 HTML 由 `templates/viewer.html` 决定：`itemize` 是项目符号，划词出现「添加批注」，右侧全局批注栏可整栏开关，栏内卡片对齐划选行。`build_review.py` 写盘即自检，失败则退出。

## 安装

```bash
git clone https://github.com/<USER>/latex-bilingual-review.git \
  ~/.cursor/skills/latex-bilingual-review
```

目录里必须有 `SKILL.md`。不要放到 `~/.cursor/skills-cursor/`。

依赖：Python 3（只用标准库）、本机已装的 Cursor。公式渲染用自带的 KaTeX，无需联网。

装好后新开一轮对话，说「生成全文中英对照」或「和某个 commit 做 Word 审阅」即可。

## 仓库里有什么

```
latex-bilingual-review/
  SKILL.md              # Agent 指令（必填）
  examples.md
  reference.md
  evals/                # itemize / sel-btn / highlight / margin
  scripts/              # extract / align / build / check_*
  templates/viewer.html
  vendor/katex/         # 离线公式
```

不要把某篇论文的 `review/*.html` 或 `*_comments.json` 提交进这个 skill 仓库。那些是论文产物，跟 skill 走会绑死一篇稿。
