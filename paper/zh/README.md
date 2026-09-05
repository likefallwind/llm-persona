# 中文阅读版

`main_zh.tex` 是正式匿名英文投稿稿 `paper/submission/main.tex` 的扩展中文阅读版。核心问题、主要发现、统计数字、结论边界和引用与英文稿对应；中文版保留了更多测量与稳健性说明，不受 ACL 八页正文限制。它用于中文审阅和团队沟通，不替代 ACL 格式的正式英文投稿件。

在仓库根目录运行：

```bash
bash scripts/build_chinese_paper.sh
```

脚本会先从冻结派生表重建中文主结果图，再输出 `paper/zh/paper_zh.pdf`。
