# 第一版：itemize 是项目符号

`build_review.py` 写出的 HTML 里，`\\begin{itemize}` 必须变成真列表。

```bash
python3 scripts/check_list_html.py
python3 scripts/check_list_html.py /path/to/review/motiondrop_bilingual.html
```

`zh` 字段仍写 `\begin{itemize}`。
