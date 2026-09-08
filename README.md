# latex-bilingual-review

Cursor Agent Skill：把 `.tex` 做成可划词批注的 HTML（中英对照 + Word 式词级审阅）。

批注存在浏览器 `localStorage`，导出 JSON 后才能入库。生成对照页需要仓库里的 `.tex`；换对比版本必须重新跑脚本，HTML 里不能现场选 git commit。

## 安装

把整个目录放到 Cursor 能扫到的 skills 路径（二选一）。

**个人（所有项目可用）：**

```bash
git clone https://github.com/<USER>/latex-bilingual-review.git \
  ~/.cursor/skills/latex-bilingual-review
```

**只给某个论文仓库：**

```bash
git clone https://github.com/<USER>/latex-bilingual-review.git \
  /path/to/paper/.cursor/skills/latex-bilingual-review
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
  scripts/              # extract / align / build
  templates/viewer.html
  vendor/katex/         # 离线公式
```

不要把某篇论文的 `review/*.html` 或 `*_comments.json` 提交进这个 skill 仓库。那些是论文产物，跟 skill 走会绑死一篇稿。

## 自己推到 GitHub

本目录目前可以独立成仓。在 GitHub 新建空仓库 `latex-bilingual-review` 后：

```bash
cd ~/.cursor/skills/latex-bilingual-review
git init -b main
git add SKILL.md README.md examples.md reference.md scripts templates vendor .gitignore
git commit -m "Add latex-bilingual-review Cursor skill."
git remote add origin git@github.com:<USER>/latex-bilingual-review.git
git push -u origin main
```

没有 `gh` 时用网页 New repository，不要勾选自动加 README（本地已有）。
