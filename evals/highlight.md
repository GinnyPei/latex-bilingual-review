# 第一版：批注黄底盖住整段选区

含公式、`[cite]`、红删/绿增的句子与纯文本一样整段黄底。`render()` 第一次画完就着色。

```bash
python3 scripts/check_highlight.py
python3 scripts/check_highlight.py /path/to/review/motiondrop_bilingual.html
```

无参数时在临时目录走一遍完整首生成。
