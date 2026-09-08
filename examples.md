# 使用示例

在论文仓库里对 agent 说话即可；不必自己跑脚本。下面是本 skill 的标准说法和对应产物。

## 例 1：第四 / 五章中英对照（最常用）

**你说：**

```
对 motiondrop.tex 的第 4、5 章生成中英对照审阅页
```

或更短：「生成第四五章中英对照」。

**agent 做：**

1. `extract_tex.py motiondrop.tex --sections 4,5` → `review/motiondrop_current.json`
2. 为每个单位补 `zh`（公式用 `$...$`，不要写 `\\(`）
3. `build_review.py` → `review/motiondrop_bilingual.html`

**你打开：** `review/motiondrop_bilingual.html`（file:// 或本地静态服务）

- 左：English / 中文并排
- 右：批注栏（划词 → 添加批注 → 导出 JSON 覆盖 `review/motiondrop_comments.json`）

本仓库已按此例生成过一页，见 `review/motiondrop_bilingual.html`。

## 例 2：全文对照

**你说：**

```
生成全文中英对照
```

去掉 `--sections`，其余同上。单位多时可按章分批写 `zh`，未译处显示「（待译）」。

## 例 3：对照 + 历史 Word 审阅

**你说：**

```
第四五章中英对照，并和 HEAD~1 做 Word 审阅对比
```

或：「和 `d62f6a5` 比」/「和 `old/motiondrop.tex` 比」。

**agent 额外做：**

```
extract_tex.py motiondrop.tex --git HEAD~1 --sections 4,5 -o review/motiondrop_old.json
align_diff.py review/motiondrop_old.json review/motiondrop_current.json -o review/motiondrop_review.json
```

页面多出 **中英对照 / Word 审阅 / 对照+审阅**。红删除线 = 旧版有、新版无；绿下划线 = 新插入。git 引用或旧 tex 路径在**生成时**选定，换一版需重新生成。

## 不要这样说

- 「改一下 tex 里的批注」→ 本 skill 不写 `.tex`
- 只说「对比一下」却不给旧版 → agent 应追问 git rev 或旧文件路径
